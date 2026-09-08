FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install OpenSSH server and required runtime packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create privilege separation directory for sshd
RUN mkdir -p /var/run/sshd

# Install Python Flask and Gunicorn production WSGI server
RUN pip install --no-cache-dir flask gunicorn

# Create non-root user ctf
RUN useradd -m -s /bin/bash ctf

WORKDIR /app

# Copy application files and SSH configuration
COPY src/ /app/
COPY src/sshd_config /etc/ssh/sshd_config

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Expose Web service (8080) and SSH service (22) for CTFd Whale multi-port forwarding
EXPOSE 8080
EXPOSE 22

# Launch container via entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
