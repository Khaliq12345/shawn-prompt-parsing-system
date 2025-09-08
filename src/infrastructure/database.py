from sqlalchemy import func
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


# ----- Metrics -----
#


# Brand Mentions
async def get_brand_mentions_db(prompt_id: str, brand: str):
    engine = get_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        # Total Mentions of Brand on this Prompt
        stmt = select(func.sum(BrandDB.mention_count)).where(
            BrandDB.prompt_id == prompt_id, BrandDB.brand_name == brand
        )
        result = await session.execute(stmt)
        mention_sum = result.scalar() or 0
    await engine.dispose()
    return mention_sum


# Brand Share of Voice
async def get_brand_sov_db(prompt_id: str, brand: str):
    engine = get_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        # Total Mentions of Brand on all Prompt
        total_stmt = select(func.sum(BrandDB.mention_count)).where(
            BrandDB.brand_name == brand
        )
        # Total Mentions of Brand on this Prompt
        brand_stmt = select(func.sum(BrandDB.mention_count)).where(
            BrandDB.prompt_id == prompt_id, BrandDB.brand_name == brand
        )
        total_mentions = (await session.execute(total_stmt)).scalar() or 0
        brand_mentions = (await session.execute(brand_stmt)).scalar() or 0
        sov = (brand_mentions / total_mentions * 100) if total_mentions else 0
    await engine.dispose()
    return round(sov, 2)


# Brand Coverage
async def get_brand_coverage_db(prompt_id: str, brand: str):
    engine = get_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        # Total Records Mentioning Brand for this Prompt
        covered_stmt = select(func.count(func.distinct(BrandDB.id))).where(
            BrandDB.prompt_id == prompt_id,
            BrandDB.brand_name == brand,
            BrandDB.mention_count > 0,
        )
        # Total Records for this Prompt Mentioning Brand or Not
        total_stmt = select(func.count(func.distinct(BrandDB.id))).where(
            BrandDB.prompt_id == prompt_id
        )
        covered = (await session.execute(covered_stmt)).scalar() or 0
        total = (await session.execute(total_stmt)).scalar() or 1
        coverage = (covered / total * 100) if total else 0
    await engine.dispose()
    return round(coverage, 2)


# Brand Position
async def get_brand_position_db(prompt_id: str, brand: str):
    engine = get_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        # Total Positions for this Prompt Mentioning Brand
        sum_stmt = select(func.sum(BrandDB.position)).where(
            BrandDB.prompt_id == prompt_id,
            BrandDB.brand_name == brand,
            BrandDB.mention_count > 0,
        )
        # Total Records Mentioning Brand for this Prompt
        count_stmt = select(func.count(func.distinct(BrandDB.id))).where(
            BrandDB.prompt_id == prompt_id,
            BrandDB.brand_name == brand,
            BrandDB.mention_count > 0,
        )
        total_position = (await session.execute(sum_stmt)).scalar() or 0
        count_mentions = (
            await session.execute(count_stmt)
        ).scalar() or 1  # éviter division par zéro
        average_position = total_position / count_mentions
    await engine.dispose()
    return round(average_position, 2)
