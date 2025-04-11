# 🎙️ Transcriber Web

A simple and secure web platform for audio transcription using [OpenAI Whisper](https://openai.com/research/whisper), powered by FastAPI, Docker, and PostgreSQL.

## 🚀 Features

- Upload and transcribe audio files (MP3, WAV, M4A, etc.)
- User registration and login system
- Transcription history
- Whisper API integration
- Language toggle (PT/EN)
- JWT authentication with secure cookies
- Responsive and mobile-friendly interface
- Deployable with Docker Compose

---

## 📦 Requirements

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- An active [OpenAI](https://platform.openai.com/account/api-keys) account and API key

---

## ⚙️ Installation

Clone the repository and create your environment file:

```bash
cp .env.example .env
# then edit the .env file to add your OPENAI_API_KEY and SECRET_KEY
```

---

## 🧪 Development

Run the platform locally with:

```bash
make run
```

Add the following line to your `/etc/hosts` file:

```bash
127.0.0.1 local.transcriber.dooloop.com.br
```

Then access via:

```
http://local.transcriber.dooloop.com.br
```

---

## 🔒 Authentication

All users must register and log in before uploading audio files. Sessions are handled via secure HTTP-only cookies using JWT.

---

## ☁️ Production Deployment

To deploy to a remote server (e.g., DigitalOcean):

```bash
# Copy the project to your server
scp -r /path/to/transcriber-web root@<YOUR_IP>:/home

# SSH into the server and start the service
docker compose up -d
```

Make sure your domain (e.g., `transcriber.dooloop.com.br`) points to your server IP.

---

## 🌍 Accessing via Custom Domain

If you're using a domain like `transcriber.dooloop.com.br`, make sure you:

1. Set up DNS pointing to your server
2. Configure `/etc/hosts` (optional for local testing)
3. Configure SSL (Let’s Encrypt via nginx-proxy + acme-companion is recommended)

---

## 📄 Example `.env`

```env
OPENAI_API_KEY=sk-...
SECRET_KEY=mysecurekey
DEFAULT_USERS=admin:admin123,tester:test123
```

---

## 💡 Tips

- Maximum file size per request: **24MB**  
- Large files are automatically split into chunks
- Transcriptions are performed using Whisper's `"whisper-1"` model
- `ffmpeg` and `ffprobe` are used internally via `pydub`

---

## 📜 License

MIT ©

---

Made with ❤️ by [Dooloop](https://dooloop.com.br)
