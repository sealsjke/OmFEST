FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    DATABASE=/data/users.db

WORKDIR /app
RUN mkdir -p /data && chown 10001:10001 /data
COPY app.py ./

USER 10001:10001
EXPOSE 8000
CMD ["python", "app.py"]
