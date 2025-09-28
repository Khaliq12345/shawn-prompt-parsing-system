import uvicorn
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes.llm_route import router as llm_router
from src.api.routes.logs import router as logs_router
from src.api.routes.metrics import router as metrics_router
from src.config.config import APP_PORT, ENV, API_KEY
from src.infrastructure.database import create_db_and_tables, dispose_engine

API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Invalid or missing API Key")


app = FastAPI(
    title="Prompt Parsing System API",
    description="API with required EndPoints - Structured",
    version="1.0.0",
    on_startup=[create_db_and_tables],
    on_shutdown=[dispose_engine],
    dependencies=[Depends(get_api_key)],
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
app.include_router(prefix="/api/logs", router=logs_router, tags=["LOGS"])
app.include_router(prefix="/api/metrics", router=metrics_router, tags=["METRICS"])


def start_app():
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=APP_PORT,
        reload=ENV != "prod",
    )
