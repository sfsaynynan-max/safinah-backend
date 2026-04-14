import os
from supabase import create_client

supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

def save_lecture_result(lecture_id: str, segments: list, sections: list):
    transcript_en = " ".join([s["text"] for s in segments])
    transcript_ar = " ".join([s.get("text_ar", "") for s in segments])
    supabase.table("lectures").update({
        "transcript_en": transcript_en,
        "transcript_ar": transcript_ar,
        "segments_json": segments,
        "sections_json": sections,
        "processing_status": "done",
    }).eq("id", lecture_id).execute()

def create_course(data: dict):
    lectures = data.pop("lectures", [])
    res = supabase.table("courses").insert({
        "title_ar": data["title_ar"],
        "title_en": data.get("title_en", ""),
        "category": data.get("category", ""),
        "source_name": data.get("source_name", ""),
        "description_ar": data.get("description_ar", ""),
        "thumbnail_url": data.get("thumbnail_url", ""),
        "status": "draft",
    }).execute()
    course_id = res.data[0]["id"]
    for i, lec in enumerate(lectures):
        supabase.table("lectures").insert({
            "course_id": course_id,
            "video_url": lec["video_url"],
            "title_ar": lec.get("title_ar", f"المقطع {i+1}"),
            "order_index": lec.get("order_index", i),
            "processing_status": "pending",
        }).execute()
    return {"id": course_id, "status": "created"}

def get_courses():
    res = supabase.table("courses").select("*").order("created_at", desc=True).execute()
    courses = res.data
    for c in courses:
        lec_res = supabase.table("lectures").select("id").eq("course_id", c["id"]).execute()
        c["lecture_count"] = len(lec_res.data)
    return courses

def get_course(course_id: str):
    res = supabase.table("courses").select("*").eq("id", course_id).single().execute()
    course = res.data
    lec_res = supabase.table("lectures").select("*").eq("course_id", course_id).order("order_index").execute()
    course["lectures"] = lec_res.data
    return course

def get_lecture(lecture_id: str):
    res = supabase.table("lectures").select("*").eq("id", lecture_id).single().execute()
    return res.data

def update_lecture(lecture_id: str, data: dict):
    supabase.table("lectures").update(data).eq("id", lecture_id).execute()

def publish_course(course_id: str):
    supabase.table("courses").update({"status": "published"}).eq("id", course_id).execute()

def unpublish_course(course_id: str):
    supabase.table("courses").update({"status": "draft"}).eq("id", course_id).execute()

def get_stats():
    published = supabase.table("courses").select("id").eq("status", "published").execute()
    done = supabase.table("lectures").select("id").eq("processing_status", "done").execute()
    pending = supabase.table("lectures").select("id").eq("processing_status", "pending").execute()
    recent = supabase.table("lectures").select("id, title_ar, processing_status, created_at, course_id").order("created_at", desc=True).limit(5).execute()
    recent_data = recent.data
    for l in recent_data:
        course = supabase.table("courses").select("title_ar").eq("id", l["course_id"]).single().execute()
        l["course_title"] = course.data["title_ar"] if course.data else "—"
    return {
        "published_courses": len(published.data),
        "done_lectures": len(done.data),
        "pending_lectures": len(pending.data),
        "recent_lectures": recent_data,
    }
