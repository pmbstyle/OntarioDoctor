#!/bin/bash
set -e

echo "🚀 Setting up Python virtual environment for OntarioDoctor..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Detect CUDA availability
echo "🔍 Detecting CUDA availability..."
if command -v nvidia-smi &> /dev/null; then
    CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}')
    echo "✓ NVIDIA GPU detected with CUDA $CUDA_VERSION"

    # Install PyTorch with CUDA support
    echo "📦 Installing PyTorch with CUDA 12.1 support..."
    pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
else
    echo "⚠️  No NVIDIA GPU detected, installing CPU-only PyTorch..."
    pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
fi

# Install other requirements (excluding torch since we just installed it)
echo "📦 Installing other dependencies..."
grep -v "^torch==" requirements.txt | grep -v "^#" | grep -v "^$" | xargs pip install

echo ""
echo "✅ Virtual environment setup complete!"
echo ""
echo "To activate the environment, run:"
echo "  source venv/bin/activate"
echo ""

# Verify installations
echo "🔍 Verifying installations..."
python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
if python -c "import torch; exit(0 if torch.cuda.is_available() else 1)" 2>/dev/null; then
    python -c "import torch; print(f'CUDA device: {torch.cuda.get_device_name(0)}')"
fi
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')"
python -c "import qdrant_client; print(f'Qdrant client installed')"
echo ""
echo "🎉 All dependencies installed successfully!"
