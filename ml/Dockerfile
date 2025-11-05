FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY predict.py .
COPY model/ ./model/

CMD ["python", "predict.py"]