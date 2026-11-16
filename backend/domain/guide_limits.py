"""Limite de pedidos por utilizador (janela deslizante, em memória).

Nota: o estado é por processo. Com vários workers, cada um conta à parte;
para um limite global passar para Redis.
"""
import time
from collections import defaultdict, deque
from typing import Callable, Deque, Dict, Tuple


class SlidingWindowLimiter:
    def __init__(self, max_calls: int, window_seconds: float, clock: Callable[[], float] = time.monotonic):
        self.max_calls = max_calls
        self.window = window_seconds
        self._clock = clock
        self._hits: Dict[int, Deque[float]] = defaultdict(deque)

    def check(self, key: int) -> Tuple[bool, float]:
        """Regista o pedido se permitido. Devolve (permitido, segundos até poder voltar a tentar)."""
        now = self._clock()
        hits = self._hits[key]
        while hits and now - hits[0] >= self.window:
            hits.popleft()
        if len(hits) >= self.max_calls:
            return False, max(self.window - (now - hits[0]), 0.0)
        hits.append(now)
        return True, 0.0
