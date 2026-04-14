from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from transcriber import transcribe
from translator import translate_segments, segment_into_sections
from database import (
    save_lecture_result, create_course, get_courses, get_course,
    update_lecture, get_lecture, publish_course, unpublish_course, get_stats
)

router = APIRouter()

# ==================== PROCESS ====================
class ProcessRequest(BaseModel):
    video_url: str
    lecture_id: str

@router.post("/process")
async def process_lecture(req: ProcessRequest):
    try:
        update_lecture(req.lecture_id, {"processing_status": "processing"})
        segments = transcribe(req.video_url)
        translated = translate_segments(segments)
        sections = segment_into_sections(translated)
        save_lecture_result(req.lecture_id, translated, sections)
        return {"lecture_id": req.lecture_id, "status": "done", "sections": sections}
    except Exception as e:
        update_lecture(req.lecture_id, {"processing_status": "error"})
        raise HTTPException(status_code=500, detail=str(e))

# ==================== COURSES ====================
class CourseCreate(BaseModel):
    title_ar: str
    title_en: Optional[str] = ""
    category: Optional[str] = ""
    source_name: Optional[str] = ""
    description_ar: Optional[str] = ""
    thumbnail_url: Optional[str] = ""
    lectures: list = []

@router.post("/courses")
def create_course_route(body: CourseCreate):
    try:
        result = create_course(body.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/courses")
def list_courses():
    try:
        return get_courses()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/courses/{course_id}")
def get_course_route(course_id: str):
    try:
        return get_course(course_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/courses/{course_id}/publish")
def publish_course_route(course_id: str):
    try:
        publish_course(course_id)
        return {"status": "published"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/courses/{course_id}/unpublish")
def unpublish_course_route(course_id: str):
    try:
        unpublish_course(course_id)
        return {"status": "draft"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== LECTURES ====================
class LectureUpdate(BaseModel):
    title_ar: Optional[str] = None
    transcript_ar: Optional[str] = None

@router.get("/lectures/{lecture_id}")
def get_lecture_route(lecture_id: str):
    try:
        return get_lecture(lecture_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/lectures/{lecture_id}")
def update_lecture_route(lecture_id: str, body: LectureUpdate):
    try:
        data = {k: v for k, v in body.dict().items() if v is not None}
        update_lecture(lecture_id, data)
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== STATS ====================
@router.get("/stats")
def stats():
    try:
        return get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== HEALTH ====================
@router.get("/health")
def health():
    return {"status": "ok"}
