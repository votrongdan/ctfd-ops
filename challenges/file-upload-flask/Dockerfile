FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ /app/
# Ensure the uploads directory is writable
RUN chmod 777 /app/uploads && chmod 777 /app/templates
USER nobody
EXPOSE 80
# Use --reload to ensure overwritten files (like templates) are reloaded
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "2", "--reload", "app:app"]
