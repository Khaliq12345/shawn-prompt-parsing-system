import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes.llm_route import router as llm_router
from src.api.routes.logs import router as logs_router
from src.api.routes.metrics import router as metrics_router
from src.config.config import ENV
from src.infrastructure.models import create_db_and_tables


app = FastAPI(
    title="Prompt Parsing System API",
    description="API with required EndPoints - Structured",
    version="1.0.0",
    on_startup=[create_db_and_tables],
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(prefix="/api/llm", router=llm_router, tags=["LLM"])
app.include_router(prefix="/api/logs", router=logs_router, tags=["Logs"])
app.include_router(prefix="/api/metrics", router=metrics_router, tags=["Metrics"])


def start_app():
    uvicorn.run(
        "src.api.app:app",
        host="localhost",
        port=8003,
        reload=ENV != "prod",
    )
