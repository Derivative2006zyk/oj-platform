from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.plugins.problem_plugin.api import router as problem_router
from app.plugins.problem_plugin.image_api import router as image_router

app = FastAPI(title="OJ Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(problem_router)
app.include_router(image_router)

@app.get("/health")
async def health():
    return {"status": "ok"}