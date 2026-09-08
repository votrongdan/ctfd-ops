FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies with pinned versions
RUN pip install --no-cache-dir flask==3.0.0 gunicorn==21.2.0 scapy==2.5.0

# Copy source code
COPY src/ /app/

# Expose port 80 for CTFd Whale compatibility
EXPOSE 80

CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "4", "app:app"]
