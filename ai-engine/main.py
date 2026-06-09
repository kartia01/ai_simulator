from __future__ import annotations

import base64
import json
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import AuthenticationError

from app import db
from app.agent import run_cascade_simulation, _get_client
from app.schemas import AdType, PersonaInput

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

_MAX_IMAGE_BYTES = 10 * 1024 * 1024   # 10 MB
_MAX_VIDEO_BYTES = 50 * 1024 * 1024   # 50 MB


# ── camelCase 변환 헬퍼 ────────────────────────────────────────────────────────

def _to_camel(snake: str) -> str:
    parts = snake.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _camel_dict(obj):
    if isinstance(obj, dict):
        return {_to_camel(k): _camel_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_camel_dict(i) for i in obj]
    return obj


# ── 앱 수명 주기 ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY is not set — simulations will fail")
    await db.init_db()
    await db.init_personas_table()
    await db.init_memory_table()
    logger.info("Ad Simulator AI Engine — startup")
    yield
    await db.close_db()
    logger.info("Ad Simulator AI Engine — shutdown")


app = FastAPI(
    title="Ad Simulator AI Engine",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# ── 공통 에러 응답 포맷 (프론트엔드 err.message 호환) ─────────────────────────

def _err(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"message": message})


# ── 시뮬레이션 실행 공통 로직 ─────────────────────────────────────────────────

_VALID_OBJECTIVES = {"awareness", "conversion"}


def _apply_target_filter(
    personas: list[PersonaInput],
    age_min: int | None,
    age_max: int | None,
    gender: str | None,
    platform: str | None,
) -> list[PersonaInput]:
    filtered = personas
    if age_min is not None:
        filtered = [p for p in filtered if p.age >= age_min]
    if age_max is not None:
        filtered = [p for p in filtered if p.age <= age_max]
    if gender:
        filtered = [p for p in filtered if p.gender and gender.lower() in p.gender.lower()]
    if platform:
        filtered = [p for p in filtered if p.platform and platform.lower() in p.platform.lower()]
    return filtered if filtered else personas


async def _run(
    ad_id: str,
    ad_content: str,
    ad_type: str,
    persona_ids: list[str],
    media_base64: str | None,
    media_content_type: str | None,
    objective: str = "conversion",
    product_price: int | None = None,
    custom_personas_raw: list[dict] | None = None,
    target_age_min: int | None = None,
    target_age_max: int | None = None,
    target_gender: str | None = None,
    target_platform: str | None = None,
) -> JSONResponse:
    has_text = len(ad_content.strip()) >= 10
    has_media = bool(media_base64)
    if not has_text and not has_media:
        return _err(400, "광고 내용(최소 10자) 또는 이미지/영상 파일 중 하나 이상 필요합니다.")

    if objective not in _VALID_OBJECTIVES:
        objective = "conversion"

    custom_personas: list[PersonaInput] = []
    for raw in (custom_personas_raw or []):
        try:
            custom_personas.append(PersonaInput(**raw))
        except Exception as exc:
            logger.warning("Invalid custom persona skipped: %s", exc)

    db_personas: list[PersonaInput] = []
    if persona_ids:
        try:
            db_personas = await db.get_personas_by_ids(persona_ids)
        except RuntimeError as exc:
            return _err(503, str(exc))
    elif not custom_personas:
        # personaIds·customPersonas 모두 없을 때만 DB 전체 로드 (API 하위 호환)
        try:
            db_personas = await db.get_all_personas()
        except RuntimeError as exc:
            return _err(503, str(exc))

    personas = db_personas + custom_personas

    has_target = any(v is not None for v in (target_age_min, target_age_max, target_gender, target_platform))
    if has_target:
        personas = _apply_target_filter(personas, target_age_min, target_age_max, target_gender, target_platform)
        logger.info("Target filter applied — %d personas remain", len(personas))

    if not personas:
        return _err(400, "시뮬레이션에 사용할 페르소나가 없습니다. 페르소나를 추가하거나 선택해 주세요.")

    is_video = media_content_type is not None and media_content_type.startswith("video/")
    safe_type = ad_type if ad_type in ("IMAGE", "VIDEO") else "IMAGE"

    logger.info("Simulation START  ad_id=%s  personas=%d  type=%s  objective=%s",
                ad_id, len(personas), safe_type, objective)

    try:
        result = await run_cascade_simulation(
            personas=personas,
            ad_content=ad_content,
            ad_id=ad_id,
            ad_type=AdType(safe_type),
            objective=objective,
            product_price=product_price,
            image_base64=None if is_video else media_base64,
            video_base64=media_base64 if is_video else None,
            media_content_type=media_content_type,
        )
    except RuntimeError as exc:
        return _err(502, str(exc))
    except Exception as exc:
        logger.error("Unexpected simulation error: %s", exc, exc_info=True)
        return _err(500, "내부 시뮬레이션 오류가 발생했습니다.")

    logger.info("Simulation DONE  ad_id=%s  VTR=%.1f%%  CTR=%.1f%%",
                ad_id, result.metrics.vtr, result.metrics.ctr)

    return JSONResponse(content=_camel_dict(result.model_dump()))


# ── 프론트엔드용 엔드포인트 ───────────────────────────────────────────────────

@app.post("/api/simulate")
async def simulate(request: Request):
    """
    JSON 또는 multipart/form-data 양쪽을 모두 처리.
    React 프론트엔드에서 직접 호출.
    """
    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type:
        form = await request.form()
        ad_id = form.get("adId", "")
        ad_content = form.get("adContent", "") or ""
        ad_type = form.get("adType", "IMAGE") or "IMAGE"
        objective = form.get("objective", "conversion") or "conversion"
        product_price_raw = form.get("productPrice")
        product_price: int | None = int(product_price_raw) if product_price_raw and product_price_raw.isdigit() else None
        media_file = form.get("mediaFile")

        media_base64 = None
        media_content_type = None

        if media_file and hasattr(media_file, "read"):
            media_bytes = await media_file.read()
            media_content_type = media_file.content_type or ""
            is_video = media_content_type.startswith("video/")
            limit = _MAX_VIDEO_BYTES if is_video else _MAX_IMAGE_BYTES
            if len(media_bytes) > limit:
                label = "영상 파일 크기는 50MB" if is_video else "이미지 파일 크기는 10MB"
                return _err(400, f"{label}를 초과할 수 없습니다.")
            media_base64 = base64.b64encode(media_bytes).decode()
            logger.info("Media received: type=%s size=%dKB", media_content_type, len(media_bytes) // 1024)

        persona_ids: list[str] = [pid for pid in form.getlist("personaIds") if pid]
        try:
            custom_personas_raw = json.loads(form.get("customPersonas") or "[]")
        except Exception:
            custom_personas_raw = []
        target_age_min = int(form.get("targetAgeMin")) if form.get("targetAgeMin") else None
        target_age_max = int(form.get("targetAgeMax")) if form.get("targetAgeMax") else None
        target_gender = form.get("targetGender") or None
        target_platform = form.get("targetPlatform") or None

    else:
        body = await request.json()
        ad_id = body.get("adId", "")
        ad_content = body.get("adContent", "") or ""
        ad_type = body.get("adType", "IMAGE") or "IMAGE"
        objective = body.get("objective", "conversion") or "conversion"
        product_price = body.get("productPrice")
        if product_price is not None and not isinstance(product_price, int):
            product_price = None
        media_base64 = body.get("mediaBase64")
        media_content_type = body.get("mediaContentType")
        persona_ids = [str(pid) for pid in (body.get("personaIds") or [])]
        custom_personas_raw = body.get("customPersonas") or []
        target = body.get("targetFilter") or {}
        target_age_min = target.get("ageMin")
        target_age_max = target.get("ageMax")
        target_gender = target.get("gender") or None
        target_platform = target.get("platform") or None

    return await _run(
        ad_id, ad_content, ad_type, persona_ids,
        media_base64, media_content_type,
        objective=objective, product_price=product_price,
        custom_personas_raw=custom_personas_raw,
        target_age_min=target_age_min,
        target_age_max=target_age_max,
        target_gender=target_gender,
        target_platform=target_platform,
    )


@app.get("/api/personas")
async def list_personas():
    try:
        personas = await db.get_all_personas()
    except RuntimeError as exc:
        return _err(503, str(exc))
    return JSONResponse(content=[p.model_dump() for p in personas])


@app.post("/api/personas", status_code=201)
async def create_persona_endpoint(request: Request):
    body = await request.json()
    try:
        persona = PersonaInput(**body)
    except Exception as exc:
        return _err(400, f"잘못된 페르소나 데이터: {exc}")
    try:
        pid = await db.create_persona(persona)
    except RuntimeError as exc:
        return _err(503, str(exc))
    except Exception as exc:
        logger.error("페르소나 생성 오류: %s", exc, exc_info=True)
        return _err(500, "페르소나 생성 중 오류가 발생했습니다.")
    return JSONResponse(content={"persona_id": pid}, status_code=201)


@app.put("/api/personas/{persona_id}")
async def update_persona_endpoint(persona_id: str, request: Request):
    body = await request.json()
    body["persona_id"] = persona_id
    try:
        persona = PersonaInput(**body)
    except Exception as exc:
        return _err(400, f"잘못된 페르소나 데이터: {exc}")
    try:
        await db.update_persona(persona)
    except RuntimeError as exc:
        return _err(503, str(exc))
    except Exception as exc:
        logger.error("페르소나 수정 오류: %s", exc, exc_info=True)
        return _err(500, "페르소나 수정 중 오류가 발생했습니다.")
    return JSONResponse(content={"ok": True})


@app.delete("/api/personas/{persona_id}")
async def delete_persona_endpoint(persona_id: str):
    try:
        await db.delete_persona(persona_id)
    except RuntimeError as exc:
        return _err(503, str(exc))
    except Exception as exc:
        logger.error("페르소나 삭제 오류: %s", exc, exc_info=True)
        return _err(500, "페르소나 삭제 중 오류가 발생했습니다.")
    return JSONResponse(content={"ok": True})


# ── 헬스체크 ─────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "ai-engine"}


@app.get("/api/health/openai")
async def health_openai():
    if not os.getenv("OPENAI_API_KEY"):
        return {"status": "error", "detail": "OPENAI_API_KEY not set"}
    try:
        response = await _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Reply with the single word: OK"}],
            max_tokens=10,
        )
        return {"status": "ok", "openai_reply": response.choices[0].message.content.strip()}
    except AuthenticationError:
        return {"status": "error", "detail": "Invalid OPENAI_API_KEY"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
