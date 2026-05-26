import asyncio
import json
import redis.asyncio as aioredis
from app.config import settings


class RedisStreamManager:
    """
    Gerenciador de Buffer de Replay SSE usando Redis Streams.
    Permite reconexão transparente e replay sem perda de pacotes.
    """
    def __init__(self):
        self._redis = None
        self._loop = None

    @property
    def redis(self):
        """Retorna a conexão ativa com o Redis para o event loop atual."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if self._redis is None or self._loop != loop:
            self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            self._loop = loop
        return self._redis

    async def add_event(self, trace_id: str, event_type: str, data: dict) -> str:
        """Adiciona um evento ao stream do Redis (buffer de replay)."""
        stream_key = f"stream:{trace_id}"
        event_payload = {
            "type": event_type,
            "data": json.dumps(data)
        }
        msg_id = await self.redis.xadd(stream_key, event_payload)
        await self.redis.expire(stream_key, 3600)  # Expira em 1 hora para evitar vazamento de memória
        return msg_id

    async def get_events_from(self, trace_id: str, last_event_id: str = "0-0") -> list[dict]:
        """Obtém todos os eventos a partir de um ID específico (replay)."""
        stream_key = f"stream:{trace_id}"
        if not last_event_id or last_event_id in ("0", "0-0"):
            start_id = "0-0"
        else:
            start_id = last_event_id

        events = await self.redis.xrange(stream_key, min=start_id, max="+")
        parsed = []
        for msg_id, payload in events:
            if msg_id == last_event_id:
                continue
            parsed.append({
                "id": msg_id,
                "type": payload.get("type"),
                "data": json.loads(payload.get("data", "{}"))
            })
        return parsed

    async def read_new_events(self, trace_id: str, last_event_id: str = "0-0", block_ms: int = 2000) -> list[dict]:
        """Aguarda e lê novos eventos a partir do último ID (bloqueante)."""
        stream_key = f"stream:{trace_id}"
        if not last_event_id or last_event_id in ("0", "0-0"):
            last_event_id = "0-0"

        res = await self.redis.xread({stream_key: last_event_id}, block=block_ms)
        parsed = []
        if res:
            for _, events in res:
                for msg_id, payload in events:
                    parsed.append({
                        "id": msg_id,
                        "type": payload.get("type"),
                        "data": json.loads(payload.get("data", "{}"))
                    })
        return parsed


redis_mgr = RedisStreamManager()
