FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY backend /app/backend
COPY shared /app/shared
COPY services/license-service /app/services/license-service

RUN pip install --no-cache-dir -r /app/backend/requirements.txt

WORKDIR /app/services/license-service

EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
