#!/bin/bash
set -e

echo "=== STARTING APPLICATION ==="

# Function to wait for service
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local timeout=${4:-60}
    
    echo "⏳ Waiting for $service_name at $host:$port..."
    
    for i in $(seq 1 $timeout); do
        if nc -z $host $port 2>/dev/null; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo "   Attempt $i/$timeout - waiting..."
        sleep 1
    done
    
    echo "❌ Timeout: $service_name not ready after ${timeout}s"
    return 1
}

# Check if running in Docker and dependencies exist
if [ -n "$DOCKER_ENV" ]; then
    # Extract host from QDRANT_URL if set, otherwise use default
    if [ -n "$QDRANT_URL" ]; then
        QDRANT_HOST=$(echo $QDRANT_URL | sed -E 's|^https?://([^:/]+).*|\1|')
    else
        QDRANT_HOST="qdrant"
    fi
    
    # Wait for dependencies
    wait_for_service "$QDRANT_HOST" "6333" "Qdrant" 120
    wait_for_service "redis" "6379" "Redis" 60
fi

# Initialize models if not already cached
echo "🔍 Checking model cache..."
if [ ! -d "/home/appuser/.cache/sentence_transformers" ] || [ ! "$(ls -A /home/appuser/.cache/sentence_transformers 2>/dev/null)" ]; then
    echo "📥 Models not found in cache. Downloading..."
    python3 -c "
import os
from pathlib import Path

# Setup cache directories
cache_dir = Path.home() / '.cache'
for subdir in ['huggingface', 'sentence_transformers', 'torch']:
    (cache_dir / subdir).mkdir(parents=True, exist_ok=True)

# Set environment variables (updated for Transformers v5+)
os.environ['HF_HOME'] = str(cache_dir / 'huggingface')
os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(cache_dir / 'sentence_transformers')
os.environ['TORCH_HOME'] = str(cache_dir / 'torch')
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# Download model
try:
    from sentence_transformers import SentenceTransformer
    print('Downloading sentence-transformers/all-MiniLM-L6-v2...')
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print('✅ Model ready!')
except Exception as e:
    print(f'❌ Model download failed: {e}')
    exit(1)
"
else
    echo "✅ Models found in cache!"
fi

# Set final environment variables (updated for Transformers v5+)
export HF_HOME="/home/appuser/.cache/huggingface"
export SENTENCE_TRANSFORMERS_HOME="/home/appuser/.cache/sentence_transformers"
export TORCH_HOME="/home/appuser/.cache/torch"
export TOKENIZERS_PARALLELISM="false"

echo "🚀 Starting application..."

# Start the application
exec "$@"