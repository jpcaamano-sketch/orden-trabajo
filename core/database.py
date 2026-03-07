"""Conexión singleton a Supabase con reintentos."""

import time
import functools
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def con_reintento(fn):
    """Decorador: reintenta 3 veces ante errores de conexión."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        global _client
        for intento in range(3):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                if intento < 2:
                    _client = None
                    time.sleep(1)
                else:
                    raise e
    return wrapper
