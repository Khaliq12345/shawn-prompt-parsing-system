from sqlmodel import select
from src.infrastructure.models import BrandDB, LlmProcess, get_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from datetime import datetime


# Save a BrandMention
async def save_brand_mention(item_lst: list[BrandDB]):
    engine = get_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        for item in item_lst:
            session.add(item)
        await session.commit()
    await engine.dispose()


# Update a LlmProcess
async def update_llm_process_status(process_id, prompt_id, status):
    engine = get_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        # create a new instance
        if status == "running":
            item = LlmProcess(
                process_id=process_id,
                prompt_id=prompt_id,
                status="running",
                date=datetime.now(),
            )
            session.add(item)
        else:
            # retrieve the process and update its status
            stmt = (
                select(LlmProcess)
                .where(LlmProcess.process_id == process_id)
                .where(LlmProcess.prompt_id == prompt_id)
            )
            process = await session.scalars(stmt)
            process = process.one()
            process.status = status
            process.date = datetime.now()
        await session.commit()
    await engine.dispose()


# Retrieve a process status
async def get_llm_process_status(process_id: str, prompt_id: str):
    engine = get_engine()
    result = None
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        stmt = (
            select(LlmProcess)
            .where(LlmProcess.process_id == process_id)
            .where(LlmProcess.prompt_id == prompt_id)
        )
        process = await session.scalars(stmt)
        process = process.one()
        result = process.status
    await engine.dispose()
    return result


# Get all BrandMention from a prompt_id
async def get_all_brand_mentions(prompt_id: str):
    engine = get_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        query = select(BrandDB).where(BrandDB.prompt_id == prompt_id)
        results = await session.execute(query)
        rows = results.scalars().all()
    await engine.dispose()
    return rows
