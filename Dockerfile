FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    postgresql-client \
    && apt-get clean

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
