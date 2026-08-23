FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir flask gunicorn

# Copy challenge files
COPY src/ /app/

# Use non-root user for security
USER nobody

# Expose port 80 for ctfd-whale compatibility
EXPOSE 80

# Start app using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "4", "app:app"]
