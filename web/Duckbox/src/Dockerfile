FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

WORKDIR /app/app

CMD ["gunicorn", \
     "--workers", "4", "--threads", "16", "--worker-class", "gthread", "--timeout", "30", "-b", "0.0.0.0:3333","app:app"]