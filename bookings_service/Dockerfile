FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bookings_service ./bookings_service

ENV PYTHONPATH=/app

EXPOSE 8002

CMD ["uvicorn", "bookings_service.app:app", "--host", "0.0.0.0", "--port", "8002"]

