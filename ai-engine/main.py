from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent import run_cascade_simulation
from app.schemas import SimulationRequest, SimulationResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Ad Simulator AI Engine — startup")
    yield
    logger.info("Ad Simulator AI Engine — shutdown")


app = FastAPI(
    title="Ad Simulator AI Engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("SPRING_BOOT_ORIGIN", "http://localhost:8080")],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.post("/simulate", response_model=SimulationResponse)
async def simulate(request: SimulationRequest):
    """
    Core simulation endpoint.
    Called exclusively by Spring Boot — not exposed to the browser directly.
    """
    logger.info(
        "Simulation START  ad_id=%s  personas=%d  type=%s",
        request.ad_id, len(request.personas), request.ad_type,
    )
    try:
        result = await run_cascade_simulation(
            personas=request.personas,
            ad_content=request.ad_content,
            ad_id=request.ad_id,
            ad_type=request.ad_type,
        )
        logger.info(
            "Simulation DONE  ad_id=%s  VTR=%.1f%%  CTR=%.1f%%",
            request.ad_id, result.metrics.vtr, result.metrics.ctr,
        )
        return result

    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal simulation error")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-engine"}
