from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import jobs, layers

app = FastAPI(title="GIS Studiegebied Tool API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(layers.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
