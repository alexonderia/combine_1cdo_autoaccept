from typing import List

try:  # pragma: no cover - optional dependency
    import torch  # type: ignore
except Exception:  # noqa: S110
    torch = None

from threading import Lock

from .config import settings
from .logger import get_logger
from .types import SourceItem
from .utils import pick_device_auto

_reranker = None
_reranker_lock = Lock()

logger = get_logger(__name__)


def get_reranker():
    global _reranker
    if _reranker is None:
        with _reranker_lock:
            if _reranker is None:
                try:
                    from FlagEmbedding import FlagReranker  # type: ignore
                except Exception as exc:  # noqa: S110
                    raise RuntimeError("FlagEmbedding is not installed") from exc
                device = pick_device_auto(settings.RERANK_DEVICE)
                try:
                    _reranker = FlagReranker(
                        settings.RERANKER_MODEL,
                        use_fp16=(device == "cuda"),
                        device=device,
                    )
                    logger.info("Reranker loaded", extra={"device": device})
                except Exception as exc:  # noqa: BLE001
                    logger.exception("Reranker failed on %s; falling back to CPU", device)
                    _reranker = FlagReranker(
                        settings.RERANKER_MODEL,
                        use_fp16=False,
                        device="cpu",
                    )
    return _reranker

def apply_rerank(query: str, sources: List[SourceItem], keep: int) -> List[SourceItem]:
    if not settings.RERANK_ENABLE or len(sources) <= keep:
        return sources[:keep]
    try:
        rr = get_reranker()
    except RuntimeError:
        return sources[:keep]
    pairs = [(query, s.text[:4000]) for s in sources]
    scores = rr.compute_score(pairs, batch_size=settings.RERANK_BATCH)
    ranked = sorted(zip(sources, scores), key=lambda x: x[1], reverse=True)
    if settings.RERANK_DEBUG:
        logger.debug(
            "Rerank scores", extra={"scores": [round(float(sc), 3) for _, sc in ranked]}
        )
    return [s for (s, sc) in ranked[:keep]]
