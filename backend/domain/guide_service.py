"""Guia Claude: assistente que orienta o utilizador dentro da aplicação.

Passagem mínima para a API do Claude. NÃO importa a base de dados nem outros serviços
de domínio (há um teste que o garante): o guia só explica, nunca altera dados.
"""
import json
import logging
import os
import time
from typing import Any, AsyncIterator, Dict, List, Tuple

import anthropic

from backend.domain.guide_knowledge import load_knowledge

logger = logging.getLogger("ceramets.guide")

DEFAULT_MODEL = "claude-haiku-5-5"
REFUSAL_TEXT = "Não consigo ajudar com isso aqui. Posso explicar-lhe como usar o CeramETS."
SseEvent = Tuple[str, Dict[str, Any]]


def guide_model() -> str:
    return os.getenv("GUIDE_MODEL", DEFAULT_MODEL)


def build_system(knowledge: str) -> List[Dict[str, Any]]:
    """Bloco estável (manual) marcado para cache. Nada volátil aqui."""
    return [{"type": "text", "text": knowledge, "cache_control": {"type": "ephemeral"}}]


def _safe_json(data: Any) -> str:
    # Impede que valores do ecrã "fechem" a tag <contexto_ecra> e injetem instruções.
    return json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e")


def build_messages(history: List[Dict[str, str]], context: Dict[str, Any], question: str) -> List[Dict[str, str]]:
    msgs = [dict(m) for m in history]
    while msgs and msgs[0]["role"] != "user":  # a API exige começar por "user"
        msgs.pop(0)
    msgs.append({
        "role": "user",
        "content": f"<contexto_ecra>{_safe_json(context)}</contexto_ecra>\n\n<pergunta>{question}</pergunta>",
    })
    return msgs


def get_client() -> anthropic.AsyncAnthropic:
    """Cliente criado a pedido; a chave vem do ambiente (ANTHROPIC_API_KEY)."""
    return anthropic.AsyncAnthropic()


def is_configured() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))


async def stream_guide(
    client: Any,
    *,
    question: str,
    context: Dict[str, Any],
    history: List[Dict[str, str]],
    user_id: int,
) -> AsyncIterator[SseEvent]:
    """Gera eventos SSE: text* → done, ou error."""
    started = time.monotonic()
    model = guide_model()
    emitted = False
    try:
        async with client.messages.stream(
            model=model,
            max_tokens=int(os.getenv("GUIDE_MAX_TOKENS", "2000")),
            output_config={"effort": "low"},
            system=build_system(load_knowledge()),
            messages=build_messages(history, context, question),
        ) as stream:
            async for delta in stream.text_stream:
                emitted = True
                yield "text", {"delta": delta}
            final = await stream.get_final_message()

        if final.stop_reason == "refusal" and not emitted:
            yield "text", {"delta": REFUSAL_TEXT}
        usage = final.usage
        info = {
            "stop_reason": final.stop_reason,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
            "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
            "latency_ms": int((time.monotonic() - started) * 1000),
        }
        # Auditoria: só metadados, nunca o texto da conversa.
        logger.info("guide user=%s ecra=%s model=%s %s", user_id, context.get("ecra"), model, info)
        yield "done", {"usage": info}
    except anthropic.RateLimitError:
        yield "error", {"mensagem": "O guia está muito solicitado. Tente novamente dentro de instantes."}
    except anthropic.APIConnectionError:
        yield "error", {"mensagem": "Não foi possível contactar o guia. Verifique a ligação e tente novamente."}
    except anthropic.APIError:
        logger.exception("guide error user=%s", user_id)
        yield "error", {"mensagem": "O guia não está disponível neste momento."}


def format_sse(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
