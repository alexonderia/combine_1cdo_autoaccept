# syntax=docker/dockerfile:1.7-labs

FROM python:3.11-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash curl jq procps iproute2 ca-certificates git build-essential && \
    rm -rf /var/lib/apt/lists/*

# === PyTorch NIGHTLY с поддержкой Blackwell (sm_120) ===
# Вариант А (CUDA 13.0):
# RUN pip install --pre --index-url https://download.pytorch.org/whl/nightly/cu130 \
#     torch torchvision torchaudio
# Если вдруг колёса cu130 недоступны в момент сборки, используйте вариант Б:
RUN pip install --pre --index-url https://download.pytorch.org/whl/nightly/cu128 \
    torch torchvision torchaudio

# Прочие тяжёлые зависимости, которые хотим кешировать в базовом слое
COPY requirements.base.txt /tmp/requirements.base.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r /tmp/requirements.base.txt

# Прогрев кэша эмбеддера (оставляем как было)
ENV HF_HOME=/root/.cache/huggingface

RUN python - <<'PY'
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-m3")
print("downloaded:", m.get_sentence_embedding_dimension())
PY

# заранее кэшируем reranker в образ
RUN --mount=type=cache,target=/root/.cache/pip \
    python - <<'PY'
from FlagEmbedding import FlagReranker
FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=False, device="cpu")
print("reranker cached in image")
PY

WORKDIR /workspace/api

FROM base AS runtime

WORKDIR /workspace/api

# Устанавливаем лёгкие зависимости, которые могут часто меняться
COPY requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r /tmp/requirements.txt

COPY app.py /workspace/api/app.py
COPY app_core /workspace/api/app_core

EXPOSE 8000
# запуск задаёт compose: command: uvicorn ...
