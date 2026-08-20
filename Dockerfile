# Dockerfile for GR00T Pico VR Teleop
# Based on install_pico.sh - Sets up the gear_sonic_teleop environment
#
# Build:
#   docker build -f Dockerfile.pico -t gr00t-pico:latest .
#
# Run:
#   docker run -it --rm gr00t-pico:latest bash
#   # or run the pico manager script:
#   docker run -it --rm gr00t-pico:latest python gear_sonic/scripts/pico_manager_thread_server.py --manager --vis_vr3pt

FROM ubuntu:22.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    ca-certificates \
    python3 \
    python3-dev \
    python3-venv \
    pkg-config \
    libssl-dev \
    libffi-dev \
    libopenblas-dev \
    liblapack-dev \
    libglfw3-dev \
    libx11-dev \
    libxrandr-dev \
    libxinerama-dev \
    libxcursor-dev \
    libxi-dev \
    libxxf86vm-dev \
    qt6-base-dev \
    libgl1-mesa-dev \
    && rm -rf /var/lib/apt/lists/*

# Set UTF-8 locale (fixes Qt warning)
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

WORKDIR /workspace

# Copy repository
COPY . /workspace/

# Install uv (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    export PATH="/root/.local/bin:$PATH" && \
    echo "export PATH=\"/root/.local/bin:\$PATH\"" >> /root/.bashrc

ENV PATH="/root/.local/bin:$PATH"

# Install uv-managed Python 3.10 and setup virtual environment
RUN uv python install 3.10 && \
    MANAGED_PY=$(uv python find --no-project 3.10) && \
    echo "Using Python: $MANAGED_PY" && \
    uv venv /workspace/.venv_teleop --python "$MANAGED_PY" --prompt gear_sonic_teleop

# Activate venv for subsequent RUN commands
ENV VIRTUAL_ENV=/workspace/.venv_teleop
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python dependencies
RUN uv pip install cmake pybind11 setuptools

# Set CMAKE_PREFIX_PATH for pybind11
RUN python -m pybind11 --cmakedir > /tmp/pybind11_dir.txt && \
    export CMAKE_PREFIX_PATH=$(cat /tmp/pybind11_dir.txt) && \
    echo "export CMAKE_PREFIX_PATH=$(cat /tmp/pybind11_dir.txt)" >> /root/.bashrc

# Install XRoboToolkit SDK
RUN uv pip install --no-build-isolation -e external_dependencies/XRoboToolkit-PC-Service-Pybind_X86_and_ARM64/

# Install gear_sonic[teleop]
RUN uv pip install -e "gear_sonic[teleop]"

# Install isaacteleop[cloudxr] for CloudXR / DeviceIO support
RUN uv pip install 'isaacteleop[cloudxr]~=1.3.0' --prerelease=allow \
    --extra-index-url https://pypi.nvidia.com || true

# Install sim extra and unitree_sdk2_python (unless you want to skip these)
# Comment out if you want a minimal image without sim dependencies
RUN uv pip install -e "gear_sonic[sim]" && \
    uv pip install -e external_dependencies/unitree_sdk2_python

# Setup CloudXR device profile
RUN echo "NV_DEVICE_PROFILE=Quest3" > /root/cloudxr.env && \
    echo "[OK] Configured CloudXR profile"

# Create startup script
RUN cat > /startup.sh <<- 'EOF'
#!/bin/bash
set -e

# Activate venv
source /workspace/.venv_teleop/bin/activate

# Set environment variables
export CMAKE_PREFIX_PATH=$(python -m pybind11 --cmakedir)

echo "============================================================"
echo "GR00T Pico VR Teleop Environment Ready"
echo "============================================================"
echo "Python: $(python --version)"
echo "Location: /workspace"
echo ""
echo "Quick start commands:"
echo "  # Run pico manager (interactive)"
echo "  python gear_sonic/scripts/pico_manager_thread_server.py --manager --vis_vr3pt"
echo ""
echo "  # Test XRT connection"
echo "  python << 'PYEOF'"
echo "import xrobotoolkit_sdk as xrt"
echo "xrt.init()"
echo "print('XRT initialized successfully')"
echo "PYEOF"
echo ""
echo "============================================================"

# Run the command passed to docker run, or bash if none
if [ $# -eq 0 ]; then
    exec bash
else
    exec "$@"
fi
EOF
chmod +x /startup.sh

# Set entrypoint
ENTRYPOINT ["/startup.sh"]

# Default command (can be overridden)
CMD ["bash"]
