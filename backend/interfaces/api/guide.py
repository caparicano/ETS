from typing import Any, AsyncIterator, Dict, List, Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
import json
import os

from backend.infrastructure.auth import get_current_user
from backend.infrastructure.models import User
from backend.domain import guide_service
from backend.domain.guide_limits import SlidingWindowLimiter

router = APIRouter()

_limiter = SlidingWindowLimiter(
    max_calls=int(os.getenv("GUIDE_RATE_MAX", "30")),
    window_seconds=float(os.getenv("GUIDE_RATE_WINDOW_SECONDS", "600")),
)


class GuideTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class GuideScreenContext(BaseModel):
    ecra: str = Field(max_length=64)
    titulo: str = Field(default="", max_length=120)
    elementosVisiveis: List[str] = Field(default_factory=list, max_length=50)
    estados: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("elementosVisiveis")
    @classmethod
    def _short_items(cls, v: List[str]) -> List[str]:
        if any(len(i) > 80 for i in v):
            raise ValueError("elemento demasiado longo")
        return v

    @field_validator("estados")
    @classmethod
    def _small_states(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if len(json.dumps(v, ensure_ascii=False)) > 8000:
            raise ValueError("estados demasiado grandes")
        return v


class GuideChatRequest(BaseModel):
    pergunta: str = Field(min_length=1, max_length=2000)
    contexto: GuideScreenContext
    historico: List[GuideTurn] = Field(default_factory=list, max_length=40)


def get_guide_client():
    if not guide_service.is_configured():
        raise HTTPException(status_code=503, detail="O guia não está configurado (falta ANTHROPIC_API_KEY).")
    return guide_service.get_client()


def enforce_rate_limit(current_user: User = Depends(get_current_user)) -> User:
    allowed, retry_after = _limiter.check(current_user.id)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Demasiados pedidos ao guia. Tente novamente mais tarde.",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )
    return current_user


@router.post("/api/v1/guide/chat")
async def guide_chat(
    request: GuideChatRequest,
    current_user: User = Depends(enforce_rate_limit),
    client=Depends(get_guide_client),
):
    """Guia do utilizador (só orienta; não acede a dados nem os altera). Resposta em SSE."""

    async def events() -> AsyncIterator[str]:
        async for name, data in guide_service.stream_guide(
            client,
            question=request.pergunta,
            context=request.contexto.model_dump(),
            history=[t.model_dump() for t in request.historico],
            user_id=current_user.id,
        ):
            yield guide_service.format_sse(name, data)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
