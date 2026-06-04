from __future__ import annotations

import base64
import logging
import os
import tempfile

# from groq import AsyncGroq
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# _VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
_VISION_MODEL = "gpt-4o-mini"
# _API_KEY = os.getenv("GROQ_API_KEY")
_API_KEY = os.getenv("OPENAI_API_KEY")

# _client: AsyncGroq | None = None
_client: AsyncOpenAI | None = None


# def _get_client() -> AsyncGroq:
def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        # _client = AsyncGroq(api_key=_API_KEY)
        _client = AsyncOpenAI(api_key=_API_KEY)
    return _client


async def build_visual_ad_description(
    ad_content: str,
    image_base64: str | None = None,
    video_base64: str | None = None,
    media_content_type: str | None = None,
) -> str:
    """
    이미지 또는 영상을 Groq 비전 모델로 분석해 광고 설명 텍스트를 반환한다.
    미디어가 없으면 원본 ad_content를 그대로 반환한다.
    """
    if image_base64:
        return await _analyze_image(ad_content, image_base64, media_content_type)
    if video_base64:
        return await _analyze_video(ad_content, video_base64)
    return ad_content


# ── Image ──────────────────────────────────────────────────────────────────────

async def _analyze_image(
    ad_content: str,
    image_base64: str,
    media_content_type: str | None,
) -> str:
    mime = media_content_type or "image/jpeg"
    data_url = f"data:{mime};base64,{image_base64}"

    extra_text = f"\n\n추가 광고 텍스트:\n{ad_content}" if ad_content.strip() else ""

    try:
        response = await _get_client().chat.completions.create(
            model=_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                        {
                            "type": "text",
                            "text": (
                                "이 이미지는 광고입니다. 광고의 시각적 요소를 분석해주세요."
                                f"{extra_text}\n\n"
                                "다음 항목을 한국어로 간결하게 작성해주세요:\n"
                                "- 헤드라인 / 주요 텍스트\n"
                                "- 색상·이미지·레이아웃 등 비주얼 특징\n"
                                "- CTA(행동 유도 문구)\n"
                                "- 전체적인 광고 메시지와 분위기\n"
                                "- 타겟 고객층이 느낄 첫인상 (1~2문장)"
                            ),
                        },
                    ],
                }
            ],
            max_tokens=700,
        )
        description = response.choices[0].message.content.strip()
        logger.info("Image analysis complete (%d chars)", len(description))
        return description

    except Exception as exc:
        logger.warning("Image analysis failed: %s — falling back to ad_content", exc)
        return ad_content


# ── Video ──────────────────────────────────────────────────────────────────────

async def _analyze_video(ad_content: str, video_base64: str) -> str:
    try:
        frames_b64, duration = _extract_key_frames(video_base64)
    except Exception as exc:
        logger.warning("Frame extraction failed: %s — falling back to ad_content", exc)
        return ad_content

    if not frames_b64:
        logger.warning("No frames extracted — falling back to ad_content")
        return ad_content

    frame_labels = ["초반", "중반", "후반"]
    analyses: list[str] = []

    for frame_b64, label in zip(frames_b64, frame_labels):
        try:
            response = await _get_client().chat.completions.create(
                model=_VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{frame_b64}"},
                            },
                            {
                                "type": "text",
                                "text": (
                                    f"이 영상 광고의 {label} 장면입니다. "
                                    "화면에 보이는 시각적 요소와 텍스트를 한국어로 간략히 설명해주세요."
                                ),
                            },
                        ],
                    }
                ],
                max_tokens=300,
            )
            analyses.append(f"[{label}] {response.choices[0].message.content.strip()}")
        except Exception as exc:
            logger.warning("Frame [%s] analysis failed: %s", label, exc)

    if not analyses:
        return ad_content

    summary = "\n".join(analyses)
    extra_text = f"\n\n추가 광고 텍스트:\n{ad_content}" if ad_content.strip() else ""
    return f"영상 광고 (길이: {duration:.1f}초)\n\n{summary}{extra_text}"


def _extract_key_frames(video_base64: str) -> tuple[list[str], float]:
    """MP4/MOV 등에서 초반·중반·후반 키프레임 3장을 추출한다."""
    import cv2  # type: ignore

    video_bytes = base64.b64decode(video_base64)

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name

    try:
        cap = cv2.VideoCapture(tmp_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        duration = total / fps

        positions = [
            max(0, int(total * 0.05)),
            max(0, total // 2),
            max(0, total - int(fps * 0.5)),
        ]

        frames_b64: list[str] = []
        for pos in positions:
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ret, frame = cap.read()
            if ret:
                _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                frames_b64.append(base64.b64encode(buf).decode("utf-8"))

        cap.release()
        return frames_b64, duration
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
