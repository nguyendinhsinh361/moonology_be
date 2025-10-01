# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy chỉ requirements trước để tận dụng cache
COPY requirements.txt .

# Cài đặt dependencies với các flag tối ưu
RUN pip install --user --no-cache-dir --no-warn-script-location \
    -r requirements.txt

# Stage 2: Runtime (nhẹ hơn)
FROM python:3.11-slim

# Tạo user không phải root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Cài đặt runtime dependencies cần thiết + CA certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages từ builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser .env .

# Set PATH
ENV PATH="/home/appuser/.local/bin:$PATH"

USER appuser

EXPOSE 8000

# Giảm số workers từ 4 xuống 2 cho t3.small
CMD ["gunicorn", "app.main:app", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]