FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Flask, Gunicorn, and PyCryptodome for dynamic prime generation
RUN pip install --no-cache-dir flask==3.0.0 gunicorn==21.2.0 pycryptodome==3.19.0

# Copy challenge files
COPY src/ /app/

# Use non-root user for security
USER nobody

# Expose port 80 for ctfd-whale
EXPOSE 80

# Run Flask using Gunicorn production server
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "4", "app:app"]
