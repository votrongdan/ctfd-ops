# Stage 1: Build C binary
FROM gcc:12 AS builder
WORKDIR /build
COPY src/chall.c .
RUN gcc -fno-stack-protector -no-pie -o chall chall.c

# Stage 2: Runtime image
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies with pinned versions
RUN pip install --no-cache-dir flask==3.0.0 gunicorn==21.2.0

# Copy binary from build stage and src files
COPY --from=builder /build/chall /app/chall
COPY src/ /app/

# Expose port 80 for CTFd Whale compatibility
EXPOSE 80

CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "4", "app:app"]
