from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import scripture_search
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def home():
    html_path = os.path.join(os.path.dirname(__file__), "frontend.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/study")
def study(q: str):
    return scripture_search.get_web_result(q)
