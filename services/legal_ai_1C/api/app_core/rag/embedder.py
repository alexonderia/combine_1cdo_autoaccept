try:  # pragma: no cover - optional dependency
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # noqa: S110
    SentenceTransformer = None  # type: ignore

from threading import Lock

from ..config import settings
from ..logger import get_logger
from ..utils import pick_device_auto

try:  # pragma: no cover
    import torch  # type: ignore
except Exception:  # noqa: S110
    torch = None

_embedder = None
_embedder_lock = Lock()

logger = get_logger(__name__)


def get_embedder() -> SentenceTransformer:
    global _embedder
    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers is not installed")
    if _embedder is None:
        with _embedder_lock:
            if _embedder is None:
                dev = pick_device_auto(settings.EMBED_DEVICE)
                try:
                    _embedder = SentenceTransformer(settings.EMBEDDING_MODEL, device=dev)
                    logger.info("Embedding model loaded", extra={"device": dev})
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Embedding init failed on %s; fallback to CPU", dev)
                    _embedder = SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")
    return _embedder
