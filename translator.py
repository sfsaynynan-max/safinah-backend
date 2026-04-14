import os
import json
import httpx

DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

TRANSLATE_PROMPT = """Translate the following educational transcript from English to Arabic.

Rules:
- Translate meaning, not words
- Write as if a knowledgeable Arab instructor is explaining directly in Arabic
- Use simple modern Arabic — clear, natural, never stiff or overly formal
- Preserve technical terms accuracy; first occurrence: العربية (English)
- Never translate code, commands, or library names
- Keep logical flow and explanation structure intact
- Output: Arabic text only, no notes or comments"""

SEGMENT_PROMPT = """قسّم النص العربي التالي إلى فقرات موضوعية منطقية.

القواعد:
- كل فقرة تمثل فكرة أو موضوع متكامل
- أعط كل فقرة عنواناً قصيراً وواضحاً
- الناتج JSON فقط بهذا الشكل:
[{"title": "عنوان الفقرة", "text": "محتوى الفقرة"}]
- بدون أي نص خارج الـ JSON"""

def _call_deepseek(system_prompt: str, user_content: str) -> str:
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.3,
    }
    response = httpx.post(DEEPSEEK_URL, json=body, headers=headers, timeout=120)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()

def translate_segments(segments: list[dict]) -> list[dict]:
    full_text = "\n".join([s["text"] for s in segments])
    translated_text = _call_deepseek(TRANSLATE_PROMPT, full_text)
    translated_lines = translated_text.split("\n")
    return [
        {**seg, "text_ar": translated_lines[i] if i < len(translated_lines) else ""}
        for i, seg in enumerate(segments)
    ]

def segment_into_sections(translated_segments: list[dict]) -> list[dict]:
    full_ar = "\n".join([s["text_ar"] for s in translated_segments if s.get("text_ar")])
    raw = _call_deepseek(SEGMENT_PROMPT, full_ar)
    clean = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)
