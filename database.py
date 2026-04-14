import os
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_lecture(lecture_id: str, segments: list, sections: list):
    transcript_en = " ".join([s["text"] for s in segments])
    transcript_ar = " ".join([s["text_ar"] for s in segments])
    supabase.table("lectures").update({
        "transcript_en": transcript_en,
        "transcript_ar": transcript_ar,
        "segments_json": segments,
        "sections_json": sections,
        "processing_status": "done",
    }).eq("id", lecture_id).execute()
