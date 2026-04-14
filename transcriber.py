import os
import yt_dlp
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

def extract_audio(video_url: str, output_path: str = "temp_audio") -> str:
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "64",
        }],
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    return f"{output_path}.mp3"

def transcribe(video_url: str) -> list[dict]:
    audio_path = extract_audio(video_url)
    try:
        with open(audio_path, "rb") as f:
            result = client.audio.transcriptions.create(
                file=f,
                model="whisper-large-v3",
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )
        return [
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
            }
            for seg in result.segments
        ]
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)
