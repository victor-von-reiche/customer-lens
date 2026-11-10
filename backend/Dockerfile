FROM python:3.12-slim
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY policies /app/policies
RUN useradd --uid 10001 --create-home appuser \
    && mkdir -p /data /app/backend/logs \
    && chown -R appuser:appuser /data /app/backend/logs
USER appuser
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
