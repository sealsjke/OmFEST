FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5555

CMD ["sh", "-c", "python init_db.py && exec python app.py"]
