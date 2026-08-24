FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ /app/
USER nobody
EXPOSE 80
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "4", "app:app"]
