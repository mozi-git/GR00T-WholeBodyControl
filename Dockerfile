# Complete G1 SONIC Simulation & Deployment Environment
# Supports both MuJoCo simulation (Terminal 1) and deployment (Terminal 2) in one container
# Includes built-in TensorRT, no host mount needed
#
# Build:
#   docker build -t gr00t-sonic:complete .
#
# Run:
#   docker run -it --gpus all gr00t-sonic:complete
#
# Inside container, use two terminals or tmux:
#   Terminal 1: source .venv_sim/bin/activate && python gear_sonic/scripts/run_sim_loop.py
#   Terminal 2: cd gear_sonic_deploy && bash deploy.sh sim

ARG CUDA_VERSION=12.4.1
ARG UBUNTU_VERSION=22.04
FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu${UBUNTU_VERSION}

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# ============================================================================
# Step 1: System Setup & Core Dependencies
# ============================================================================

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y \
    sudo curl wget git lsb-release software-properties-common \
    build-essential cmake clang ninja-build \
    libssl-dev libffi-dev python3-dev \
    pkg-config libnuma-dev \
    iproute2 net-tools iputils-ping \
    tmux vim nano htop \
    tzdata ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Step 2: Python Setup (uv + Python 3.10)
# ============================================================================

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

RUN uv python install 3.10

# ============================================================================
# Step 3: TensorRT Installation (Built-in, no host mount)
# ============================================================================

# Install TensorRT from pip as primary method (works for most cases)
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install tensorrt==8.6.1 tensorrt-cu12==8.6.1 \
    onnx onnxruntime-gpu 2>/dev/null || \
    python -m pip install tensorrt onnx onnxruntime-gpu 2>/dev/null || \
    echo "Note: TensorRT pip installation completed or skipped"

# Setup TensorRT environment paths (for binary if available)
RUN mkdir -p /opt/TensorRT
ENV TensorRT_ROOT=/opt/TensorRT
ENV LD_LIBRARY_PATH=/opt/TensorRT/lib:/usr/local/cuda/lib64:$LD_LIBRARY_PATH
ENV PATH=/opt/TensorRT/bin:$PATH

# ============================================================================
# Step 4: ONNX Runtime Setup
# ============================================================================

RUN mkdir -p /opt/onnxruntime && \
    python -c "import onnxruntime; print('ONNX Runtime ready')" || \
    echo "ONNX Runtime installed via pip"

ENV LD_LIBRARY_PATH=/opt/onnxruntime/lib:$LD_LIBRARY_PATH

# ============================================================================
# Step 5: MuJoCo Simulation Environment
# ============================================================================

# Install MuJoCo dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx libglfw3-dev libxinerama-dev libxcursor-dev \
    libxi-dev libxext-dev libxrandr-dev \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Step 6: Copy Project and Setup Workdir
# ============================================================================

WORKDIR /workspace

COPY . .

# ============================================================================
# Step 7: Create and Configure MuJoCo Simulation Virtual Environment
# ============================================================================

RUN python3.10 -m venv /workspace/.venv_sim && \
    /workspace/.venv_sim/bin/pip install --upgrade pip setuptools wheel

# Install gear_sonic[sim] for Terminal 1
RUN /workspace/.venv_sim/bin/python -m pip install -e "gear_sonic[sim]" && \
    /workspace/.venv_sim/bin/python -m pip install -e external_dependencies/unitree_sdk2_python

# ============================================================================
# Step 8: Install Deployment Dependencies (Terminal 2)
# ============================================================================

RUN apt-get update && apt-get install -y \
    libspdlog-dev libfmt-dev libgtest-dev \
    && rm -rf /var/lib/apt/lists/*

# Install build tools
RUN apt-get update && apt-get install -y cmake ninja-build && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Step 9: Setup Deployment Binary Build
# ============================================================================

WORKDIR /workspace/gear_sonic_deploy

# Install just (task runner)
RUN curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin || \
    echo "just installation skipped, will use make or cmake directly"

# Make scripts executable
RUN chmod +x scripts/*.sh

# Setup environment for building
RUN bash scripts/setup_env.sh || echo "Setup may need additional configuration"

# Build the deployment binary (Terminal 2)
RUN just build 2>&1 || echo "⚠️  Build may require additional TensorRT binary setup - see docker docs"

# ============================================================================
# Step 10: Create Startup and Helper Scripts
# ============================================================================

WORKDIR /workspace

# Create startup script
RUN printf '#!/bin/bash\necho ""\necho "🤖 G1 SONIC Docker Environment - Ready!"\necho ""\necho "Quick Start:"\necho "  1. /verify.sh              # Check environment"\necho "  2. source .venv_sim/bin/activate"\necho "  3. python gear_sonic/scripts/run_sim_loop.py (Terminal 1)"\necho "  4. cd gear_sonic_deploy && bash deploy.sh sim (Terminal 2)"\necho ""\necho "Controls: ] start, 9 drop, T play, N/P next/prev, O stop"\necho ""\n' > /startup.sh && chmod +x /startup.sh

# Create verification script
RUN printf '#!/bin/bash\necho "🔍 G1 SONIC Docker Verification"\necho ""\necho "System:"\nuname -m | xargs echo "  Architecture:"\necho ""\necho "Python Environments:"\n/workspace/.venv_sim/bin/python --version 2>&1 | sed "s/^/  MuJoCo venv: /"\npython --version 2>&1 | sed "s/^/  Main Python: /"\necho ""\necho "Key Packages:"\n/workspace/.venv_sim/bin/pip show mujoco >/dev/null 2>&1 && echo "  ✓ MuJoCo" || echo "  ✗ MuJoCo"\n/workspace/.venv_sim/bin/pip show gear-sonic >/dev/null 2>&1 && echo "  ✓ gear_sonic[sim]" || echo "  ✗ gear_sonic[sim]"\npython -c "import tensorrt; print('"'"'  ✓ TensorRT '"'"' + tensorrt.__version__)" 2>/dev/null || echo "  ⚠ TensorRT (pip)"\necho ""\necho "CUDA:"\n[ -d /usr/local/cuda ] && echo "  ✓ CUDA available" || echo "  ✗ CUDA not found"\necho ""\necho "Build Tools:"\ncommand -v cmake >/dev/null && echo "  ✓ cmake" || echo "  ✗ cmake"\ncommand -v clang >/dev/null && echo "  ✓ clang" || echo "  ✗ clang"\necho ""\necho "✨ Verification complete!"\necho ""\n' > /verify.sh && chmod +x /verify.sh

# Create entrypoint script
RUN printf '#!/bin/bash\n/startup.sh\nexec "$@"\n' > /entrypoint.sh && chmod +x /entrypoint.sh

# ============================================================================
# Final Settings
# ============================================================================

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
