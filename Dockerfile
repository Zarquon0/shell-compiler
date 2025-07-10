FROM ubuntu:latest

#Set python environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VENV_PATH=/home/shell-compiler/.venv

# Install base dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    git \
    curl \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /home/shell-compiler

# Create virtual environment
RUN python3.12 -m venv $VENV_PATH

# Activate virtualenv and install Python deps
COPY requirements.txt .

# Use full path to pip inside venv
RUN $VENV_PATH/bin/pip install --upgrade pip && \
    $VENV_PATH/bin/pip install -r requirements.txt

# Clone and install binpash/libdash and dependencies using venv python
RUN apt-get update && apt-get install -y \
  libtool \
  autoconf \
  automake
RUN git clone https://github.com/binpash/libdash.git /opt/libdash && \
    $VENV_PATH/bin/pip install /opt/libdash

# Optional: Add venv binaries to PATH
ENV PATH="$VENV_PATH/bin:$PATH"

# Create the src directory (to be mounted)
RUN mkdir -p /home/shell-compiler/src

# Default to bash
CMD [ "/bin/bash" ]

# Run bash shell start up script (source cargo) 
# COPY docker-helpers/startup.sh /
# RUN chmod +x /startup.sh
# ENTRYPOINT [ "/startup.sh" ]
# SHELL ["/bin/bash", "-c"]
# CMD [ "/bin/bash" ]