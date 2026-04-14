import os
import re
import httpx
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

PIPED_API = "https://pipedapi.kavin.rocks"

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

def get_youtube_transcript(video_id: str) -> list[dict]:
    from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
    return [
        {
            "start": entry["start"],
            "end": entry["start"] + entry["duration"],
            "text": entry["text"].strip(),
        }
        for entry in transcript
    ]

def get_audio_via_piped(video_id: str) -> str:
    res = httpx.get(f"{PIPED_API}/streams/{video_id}", timeout=30)
    res.raise_for_status()
    data = res.json()
    audio_streams = [s for s in data.get("audioStreams", []) if not s.get("videoOnly")]
    if not audio_streams:
        raise ValueError("لا يوجد صوت متاح من Piped")
    best = sorted(audio_streams, key=lambda s: s.get("bitrate", 0), reverse=True)[0]
    return best["url"]

def transcribe_via_whisper(audio_url: str) -> list[dict]:
    audio_path = "/tmp/temp_audio.mp3"
    with httpx.stream("GET", audio_url, timeout=120, follow_redirects=True) as r:
        r.raise_for_status()
        with open(audio_path, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
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

def transcribe(video_url: str) -> list[dict]:
    video_id = extract_video_id(video_url)

    # الحالة 1: جرب transcript مباشرة
    try:
        segments = get_youtube_transcript(video_id)
        print(f"✅ transcript جاهز: {len(segments)} مقطع")
        return segments
    except Exception as e:
        print(f"⚠️ لا يوجد transcript: {e}")

    # الحالة 2: Piped + Whisper
    print("🎵 جاري الحصول على الصوت من Piped...")
    audio_url = get_audio_via_piped(video_id)
    print("🎙️ جاري تحويل الصوت لنص...")
    return transcribe_via_whisper(audio_url)
