FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY policies/ policies/

EXPOSE 8000

CMD ["python", "src/gateway.py"]
