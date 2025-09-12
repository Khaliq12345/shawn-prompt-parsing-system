FROM ubuntu:24.04

# Install dependencies: curl, certificates, build tools, Python 3.12 and pip
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        build-essential \
        software-properties-common \
        lsb-release \
        wget \
        gnupg \
        libffi-dev \
        libssl-dev \
        zlib1g-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        libncursesw5-dev \
        xz-utils \
        tk-dev \
        uuid-dev \
        liblzma-dev \
        xclip \
        git && \
    apt-get update && \
    rm -rf /var/lib/apt/lists/*

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install Python dependencies
RUN uv sync --locked
