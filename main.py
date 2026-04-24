from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import scripture_search
import access
import os
from stripe_routes import router as stripe_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    access.init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stripe_router)


def _read_template(rel_path: str) -> str:
    path = os.path.join(os.path.dirname(__file__), rel_path)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/", response_class=HTMLResponse)
def home():
    return _read_template("frontend.html")


@app.get("/unlock", response_class=HTMLResponse)
def unlock_page():
    return _read_template("templates/unlock.html")


@app.get("/study")
def study(q: str, show_all: bool = False):
    return scripture_search.get_web_result(q, show_all=show_all)


class CodeRequest(BaseModel):
    code: str


@app.post("/api/validate-code")
def validate_code(body: CodeRequest):
    if access.validate_code(body.code.strip().upper()):
        return {"valid": True}
    raise HTTPException(status_code=403, detail="Invalid access code")
