FROM yuanli-ai-acr-registry.cn-shanghai.cr.aliyuncs.com/demo/locomotion:sonic-trtsim

# Accept build argument for username
ARG USERNAME=root
ARG USERID=0
ARG HOME_DIR=/root

# Install uv if not already present
RUN if ! command -v uv &> /dev/null; then \
        curl -LsSf https://astral.sh/uv/install.sh | sh; \
    fi

# Create .venv_teleop directory
RUN mkdir -p ${HOME_DIR}/.venv_teleop

# Create venv_teleop using uv
RUN uv venv --python 3.10 ${HOME_DIR}/.venv_teleop

# Install gear_sonic[teleop] dependencies
# Using uv pip with --python to target the specific venv
RUN uv pip install --python ${HOME_DIR}/.venv_teleop/bin/python pyzmq msgpack msgpack-numpy pin pyvista

# Install gear_sonic[teleop] from the workspace
# Note: Base image (sonic-trtsim) already has project code at /workspace
RUN uv pip install --python ${HOME_DIR}/.venv_teleop/bin/python -e /workspace/gear_sonic[teleop]

# Add activation of venv_teleop to bashrc for convenience
RUN echo "" >> ${HOME_DIR}/.bashrc && \
    echo "# Virtual environment for teleop" >> ${HOME_DIR}/.bashrc && \
    echo "export VENV_TELEOP=${HOME_DIR}/.venv_teleop" >> ${HOME_DIR}/.bashrc && \
    echo "# To activate teleop venv, run: source \$VENV_TELEOP/bin/activate" >> ${HOME_DIR}/.bashrc

# Default command (can be overridden at runtime)
CMD ["/bin/bash"]