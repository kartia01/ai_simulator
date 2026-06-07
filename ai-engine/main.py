from __future__ import annotations

import base64
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
from app.schemas import AdType

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
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── 공통 에러 응답 포맷 (프론트엔드 err.message 호환) ─────────────────────────

def _err(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"message": message})


# ── 시뮬레이션 실행 공통 로직 ─────────────────────────────────────────────────

_VALID_OBJECTIVES = {"awareness", "conversion"}


async def _run(
    ad_id: str,
    ad_content: str,
    ad_type: str,
    persona_ids: list[str],
    media_base64: str | None,
    media_content_type: str | None,
    objective: str = "conversion",
    product_price: int | None = None,
) -> JSONResponse:
    has_text = len(ad_content.strip()) >= 10
    has_media = bool(media_base64)
    if not has_text and not has_media:
        return _err(400, "광고 내용(최소 10자) 또는 이미지/영상 파일 중 하나 이상 필요합니다.")

    if objective not in _VALID_OBJECTIVES:
        objective = "conversion"

    try:
        personas = (
            await db.get_personas_by_ids(persona_ids)
            if persona_ids
            else await db.get_all_personas()
        )
    except RuntimeError as exc:
        return _err(503, str(exc))

    if not personas:
        return _err(400, "No personas found — seed the database first")

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

    return await _run(
        ad_id, ad_content, ad_type, persona_ids,
        media_base64, media_content_type,
        objective=objective, product_price=product_price,
    )


@app.get("/api/personas")
async def list_personas():
    try:
        personas = await db.get_all_personas()
    except RuntimeError as exc:
        return _err(503, str(exc))
    return JSONResponse(content=[p.model_dump() for p in personas])


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
