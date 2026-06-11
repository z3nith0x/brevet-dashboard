import os
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from pydantic import BaseModel

from .brevet import fetch_and_calculate

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

app = FastAPI(title="Brevet 2026 - Controle Continu", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HERE = Path(__file__).resolve().parent
PUBLIC = HERE.parent / "public"


class LoginRequest(BaseModel):
    url: str
    username: str
    password: str
    ent: str = ""


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/calculate")
def calculate(req: LoginRequest):
    return fetch_and_calculate(
        url=req.url,
        login=req.username,
        password=req.password,
        ent=req.ent,
    )


# Catch-all: serve frontend files (works on Vercel AND locally)
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    if not PUBLIC.is_dir():
        return {"error": "public directory not found"}
    file = PUBLIC / full_path
    if file.is_file():
        return FileResponse(str(file))
    index = PUBLIC / "index.html"
    if index.is_file():
        return FileResponse(str(index))
    return {"error": "not found"}
