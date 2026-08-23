# Stage 1: Build C binary
FROM gcc:12 AS builder
WORKDIR /build
COPY src/chall.c .
RUN gcc -fno-stack-protector -no-pie -o chall chall.c

# Stage 2: Runtime TCP service
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install socat for TCP port forwarding
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends socat && \
    rm -rf /var/lib/apt/lists/*

# Copy binary from build stage and entrypoint
COPY --from=builder /build/chall /app/chall
COPY src/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh /app/chall

# Expose TCP port 1337 for direct CTFd Whale netcat connection
EXPOSE 1337

ENTRYPOINT ["/app/entrypoint.sh"]
