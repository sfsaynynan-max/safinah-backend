from fastapi import FastAPI
from routes import router

app = FastAPI(title="السفينة API")
app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {"status": "السفينة تعمل ✅"}
