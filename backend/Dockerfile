# Backend image for SafetyLens Stage 7
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV PYTHONUNBUFFERED=1 \
    APP_NAME="SafetyLens API" \
    ENVIRONMENT=production \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    DEMO_MODE=true \
    AI_PROVIDER=demo \
    AI_DEMO_MODE=true \
    PLANNER_PROVIDER=demo \
    UPLOAD_DIRECTORY=/data/uploads \
    FRAME_DIRECTORY=/data/frames \
    PROCEDURE_DIRECTORY=/data/procedures \
    REPORT_DIRECTORY=/data/reports \
    DETECTOR_EVENTS_DIRECTORY=/data/detector-events \
    DATABASE_URL=sqlite:////data/safetylens.db \
    FRONTEND_ORIGINS=http://localhost:3000

EXPOSE 8000

CMD ["sh", "-c", "python -m app.seed.run && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
