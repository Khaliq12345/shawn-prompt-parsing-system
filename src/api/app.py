import uvicorn
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1.metrics import router as metrics_router
from src.api.v1.prompts import router as prompts_router
from src.api.v1.logs import router as log_router
from src.config.config import APP_PORT, ENV, API_KEY
from src.infrastructure.database import DataBase
from src.infrastructure.click_house import ClickHouse

database = DataBase()

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
    on_startup=[database.create_all_tables, ClickHouse().create_table],
    on_shutdown=[database.engine.dispose],
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
app.include_router(prefix="/api", router=metrics_router, tags=["METRICS"])
app.include_router(prefix="/api", router=prompts_router, tags=["PROMPTS"])
app.include_router(prefix="/api", router=log_router, tags=["LOGS"])


def start_app():
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=APP_PORT,
        reload=ENV != "prod",
    )
