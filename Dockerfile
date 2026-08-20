FROM yuanli-ai-acr-registry.cn-shanghai.cr.aliyuncs.com/demo/locomotion:sonic-teleop

# Accept build argument for username
ARG USERNAME=root
ARG USERID=0
ARG HOME_DIR=/root

# Install uv if not already present
RUN if ! command -v uv &> /dev/null; then \
        curl -LsSf https://astral.sh/uv/install.sh | sh; \
    fi

# Install cmake + pybind11 for XRoboToolkit SDK build
RUN uv pip install --python ${HOME_DIR}/.venv_teleop/bin/python cmake pybind11 setuptools

# Set CMAKE_PREFIX_PATH for pybind11
ENV CMAKE_PREFIX_PATH=${HOME_DIR}/.venv_teleop/lib/python3.10/site-packages/pybind11/share/cmake/pybind11

# Install XRoboToolkit SDK (CMake-based Python bindings)
RUN uv pip install --python ${HOME_DIR}/.venv_teleop/bin/python --no-build-isolation \
    -e /workspace/external_dependencies/XRoboToolkit-PC-Service-Pybind_X86_and_ARM64/

# Install isaacteleop[cloudxr] for CloudXR / DeviceIO path
RUN uv pip install --python ${HOME_DIR}/.venv_teleop/bin/python 'isaacteleop[cloudxr]~=1.3.0' --prerelease=allow \
    --extra-index-url https://pypi.nvidia.com

# Seed ~/cloudxr.env with the device profile
RUN echo "NV_DEVICE_PROFILE=Quest3" > ${HOME_DIR}/cloudxr.env

# Add activation of venv_teleop to bashrc for convenience
RUN echo "" >> ${HOME_DIR}/.bashrc && \
    echo "# Virtual environment for teleop" >> ${HOME_DIR}/.bashrc && \
    echo "export VENV_TELEOP=${HOME_DIR}/.venv_teleop" >> ${HOME_DIR}/.bashrc && \
    echo "# To activate teleop venv, run: source \$VENV_TELEOP/bin/activate" >> ${HOME_DIR}/.bashrc

# Default command (can be overridden at runtime)
CMD ["/bin/bash"]