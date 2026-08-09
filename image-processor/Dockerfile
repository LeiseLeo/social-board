FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY processor.py .

CMD ["python", "/app/processor.py", "--input", "/images/original", "--output", "/images/generated"]