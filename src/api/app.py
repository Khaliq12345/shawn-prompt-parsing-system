import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes.llm_route import router as llm_router
from src.api.routes.logs import router as logs_router
from src.config.config import ENV
from src.infrastructure.models import create_db_and_tables
from redis.asyncio import ConnectionPool
from src.infrastructure.taskiq_app import broker
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    print("Application starting...")
    await create_db_and_tables()
    if not broker.is_worker_process:
        print("Starting broker")
        await broker.startup()
    print("Creating redis pool")
    app.state.redis_pool = ConnectionPool.from_url("redis://localhost")

    yield

    # --- Shutdown ---
    print("Application shutting down...")
    if not broker.is_worker_process:
        print("Shutting down broker")
        await broker.shutdown()
    print("Stopping redis pool")
    await app.state.redis_pool.disconnect()


app = FastAPI(
    title="Prompt Parsing System API",
    description="API with required EndPoints - Structured",
    version="1.0.0",
    # on_startup=[create_db_and_tables],
    lifespan=lifespan,
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
app.include_router(prefix="/api", router=llm_router, tags=["LLM"])
app.include_router(prefix="/api", router=logs_router, tags=["Logs"])


def start_app():
    uvicorn.run(
        "src.api.app:app",
        host="localhost",
        port=8003,
        reload=ENV != "prod",
    )
