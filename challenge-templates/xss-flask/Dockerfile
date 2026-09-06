FROM python:3.10-slim

# Install Chromium and driver for the bot
RUN apt-get update && \
    apt-get install -y chromium chromium-driver && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/

# CAREFUL: Do not run as 'nobody' because Chromium might need specific permissions 
# or a proper home directory. We will create a non-root user.
RUN useradd -m ctfuser
USER ctfuser

EXPOSE 80

# RUNTIME: Run the app on 80
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "2", "app:app"]
