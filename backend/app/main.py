from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import uploads, dashboard, rules

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TransactIQ API",
    description="Transaction Validation & Processing Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(uploads.router)
app.include_router(dashboard.router)
app.include_router(rules.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "TransactIQ API"}
