# System image for Cursor Cloud Agents.
# Do not COPY the project here — Cursor checks out the repo separately.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    UV_LINK_MODE=copy \
    PATH="/usr/local/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    build-essential \
    python3 \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install uv into /usr/local so every user on the VM can run it.
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && install -m 0755 /root/.local/bin/uv /usr/local/bin/uv \
    && install -m 0755 /root/.local/bin/uvx /usr/local/bin/uvx \
    && uv --version

# Pre-fetch the project Python so first `uv sync` is faster.
RUN uv python install 3.12
