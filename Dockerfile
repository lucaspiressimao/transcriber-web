FROM python:3.11-slim

# Adiciona ffmpeg (que inclui ffprobe)
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
