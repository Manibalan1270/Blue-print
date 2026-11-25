FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

COPY requirements.txt .
# CPU-only PyTorch: the default CUDA build adds ~2GB to the image for no benefit here.
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels torch --index-url https://download.pytorch.org/whl/cpu && \
    pip wheel --no-cache-dir --wheel-dir /wheels --find-links=/wheels -r requirements.txt


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
