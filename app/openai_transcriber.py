from openai import OpenAI
import os
import math
import tempfile
import subprocess
import uuid
from pydub import AudioSegment
from fastapi import UploadFile

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Tamanho máximo permitido por segmento (em bytes)
MAX_FILE_SIZE = 24 * 1024 * 1024  # 24MB

def convert_to_wav(input_path: str) -> str:
    output_path = f"/tmp/{uuid.uuid4().hex}.wav"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, output_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Erro ao converter {input_path} para wav: {e}")
        raise Exception("Falha ao converter áudio para WAV.")
    
def is_valid_audio(file_path: str) -> bool:
    try:
        result = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", file_path, "-f", "null", "-"],
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL
        )
        return result.returncode == 0
    except Exception as e:
        print("Erro ao validar áudio:", e)
        return False
    
def split_audio_by_size(file_path, max_size=MAX_FILE_SIZE):
    """Divide o áudio em segmentos menores para evitar erro 413."""
    audio = AudioSegment.from_file(file_path)
    file_size = os.path.getsize(file_path)

    if file_size <= max_size:
        return [file_path]

    num_segments = math.ceil(file_size / max_size)
    segment_length = len(audio) / num_segments  # Duração por segmento

    segments = []
    for i in range(num_segments):
        start_time = i * segment_length
        end_time = min((i + 1) * segment_length, len(audio))

        segment = audio[start_time:end_time]
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        segment.export(temp_file.name, format="wav")
        segments.append(temp_file.name)

    return segments

def transcribe_audio(file_path):
    # Converte para .wav antes de tudo
    converted_path = convert_to_wav(file_path)

    segments = split_audio_by_size(converted_path)

    transcriptions = []
    for segment in segments:
        with open(segment, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            transcriptions.append(response.text)

        if segment != converted_path:
            os.remove(segment)

    if converted_path != file_path:
        os.remove(converted_path)

    return " ".join(transcriptions)


async def transcribe_uploaded_file(uploaded_file: UploadFile) -> str:
    """Lida com UploadFile do FastAPI e chama a transcrição real."""
    suffix = os.path.splitext(uploaded_file.filename)[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        with open(tmp.name, "wb") as buffer:
            while True:
                chunk = await uploaded_file.read(1024 * 1024)
                if not chunk:
                    break
                buffer.write(chunk)
        tmp_path = tmp.name

    try:
        if not is_valid_audio(tmp_path):
            raise HTTPException(status_code=400, detail="Arquivo de áudio corrompido ou inválido.")
        return transcribe_audio(tmp_path)
    finally:
        os.remove(tmp_path)
