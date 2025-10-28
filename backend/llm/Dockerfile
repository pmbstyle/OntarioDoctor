FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Install Python
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install vLLM
RUN pip install --no-cache-dir vllm==0.6.3.post1

# Copy startup script
COPY backend/llm/run_vllm.sh .
RUN chmod +x run_vllm.sh

# Expose port
EXPOSE 8000

# Run vLLM
CMD ["./run_vllm.sh"]
