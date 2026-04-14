from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from transcriber import transcribe
from translator import translate_segments, segment_into_sections

router = APIRouter()

class ProcessRequest(BaseModel):
    video_url: str
    lecture_id: str

@router.post("/process")
async def process_lecture(req: ProcessRequest):
    try:
        segments = transcribe(req.video_url)
        translated = translate_segments(segments)
        sections = segment_into_sections(translated)
        return {
            "lecture_id": req.lecture_id,
            "segments": translated,
            "sections": sections,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def health():
    return {"status": "ok"}
