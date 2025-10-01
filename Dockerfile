# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy requirements trước để tận dụng cache
COPY requirements.txt .

# Cài đặt dependencies với các flag tối ưu
RUN pip install --user --no-cache-dir --no-warn-script-location \
    -r requirements.txt

# Stage 2: Runtime (nhẹ hơn)
FROM python:3.11-slim

# Tạo user không phải root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Cài đặt chỉ runtime dependencies cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages từ builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser .env .

# Set PATH to include user's local bin directory
ENV PATH="/home/appuser/.local/bin:$PATH"

USER appuser

EXPOSE 8000

# Giảm workers cho t3.small (2 workers thay vì 4)
CMD ["gunicorn", "app.main:app", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]