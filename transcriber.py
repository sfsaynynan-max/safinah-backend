import re
from youtube_transcript_api import YouTubeTranscriptApi

def extract_video_id(url: str) -> str:
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise ValueError("رابط YouTube غير صالح")

def transcribe(video_url: str) -> list[dict]:
    video_id = extract_video_id(video_url)
    ytt = YouTubeTranscriptApi()
    transcript = ytt.fetch(video_id)
    return [
        {
            "start": entry.start,
            "end": entry.start + entry.duration,
            "text": entry.text.strip(),
        }
        for entry in transcript
    ]
