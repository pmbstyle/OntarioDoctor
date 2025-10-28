#!/bin/bash
set -e

echo "🚀 Starting vLLM server with Meditron-7B..."

# Load configuration
MODEL="${VLLM_MODEL:-epfl-llm/meditron-7b}"
PORT="${VLLM_PORT:-8000}"
HOST="${VLLM_HOST:-0.0.0.0}"

echo "Model: $MODEL"
echo "Port: $PORT"
echo "Host: $HOST"
echo "Letting vLLM auto-detect optimal GPU memory and context length settings..."

# Detect CUDA availability
if command -v nvidia-smi &> /dev/null; then
    CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}')
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n 1)
    echo "✓ NVIDIA GPU detected: $GPU_NAME (CUDA $CUDA_VERSION)"

    # Set CUDA device if not already set
    if [ -z "$CUDA_VISIBLE_DEVICES" ]; then
        export CUDA_VISIBLE_DEVICES=0
        echo "✓ Using GPU device 0"
    else
        echo "✓ Using GPU device(s): $CUDA_VISIBLE_DEVICES"
    fi

    # Run vLLM with GPU (Meditron-7B is Llama-2 based, fully supported)
    # Let vLLM auto-configure optimal settings for 16GB GPU
    echo "🚀 Starting vLLM with GPU acceleration (auto-config)..."
    python3 -m vllm.entrypoints.openai.api_server \
        --model "$MODEL" \
        --host "$HOST" \
        --port "$PORT" \
        --tensor-parallel-size 1 \
        --dtype auto \
        --trust-remote-code

else
    echo "⚠️  No NVIDIA GPU detected"
    echo "❌ vLLM requires GPU support. CPU-only mode is not recommended for production."
    echo ""
    echo "For development/testing without GPU, consider using:"
    echo "  - Ollama (local CPU inference)"
    echo "  - OpenAI API (cloud)"
    echo "  - HuggingFace Inference Endpoints"
    echo ""
    exit 1
fi
