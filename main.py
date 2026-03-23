from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import scripture_search

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Online", "ministry": "Ke Aupuni O Ke Akua"}

@app.get("/study")
def study(q: str):
    return scripture_search.get_web_result(q)