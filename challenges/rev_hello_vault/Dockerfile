# Stage 1: GCC environment for building binary
FROM gcc:12 AS builder
WORKDIR /build

# Stage 2: Runtime image
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install gcc and python dependencies with pinned versions
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir flask==3.0.0 gunicorn==21.2.0

# Copy src files
COPY src/ /app/

# Expose port 80 for CTFd Whale compatibility
EXPOSE 80

CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "4", "app:app"]
