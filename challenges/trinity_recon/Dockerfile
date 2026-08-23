FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install OpenSSH server
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/run/sshd

# Install Python packages for Web (Flask) and FTP (pyftpdlib)
RUN pip install --no-cache-dir flask gunicorn pyftpdlib

# Create user 'trinity'
RUN useradd -m -s /bin/bash trinity
# Set the password for SSH
RUN echo 'trinity:follow_the_white_rabbit_2026' | chpasswd

# Setup FTP data directory
RUN mkdir -p /ftp_data
RUN echo "SSH_USER=trinity\nSSH_PASS=follow_the_white_rabbit_2026\n" > /ftp_data/backup_creds.txt
RUN chmod -R 755 /ftp_data

WORKDIR /app

# Copy app files
COPY src/ /app/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose Web (8080), FTP (2121), and SSH (22)
EXPOSE 8080 2121 22

ENTRYPOINT ["/entrypoint.sh"]
