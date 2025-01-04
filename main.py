from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import router

origins = [
    "http://localhost:8000",
    "http://localhost:5173",
    "http://localhost:5174",
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
