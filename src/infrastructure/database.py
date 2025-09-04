from sqlmodel import select
from src.infrastructure.models import BrandMentionDB, get_engine
from sqlalchemy.ext.asyncio import async_sessionmaker


# Save a BrandMention
async def save_brand_mention(item: BrandMentionDB):
    engine = get_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        session.add(item)
        await session.commit()
    await engine.dispose()


# Get all BrandMention from a process_id
async def get_all_brand_mentions(process_id: str):
    engine = get_engine()
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        query = select(BrandMentionDB).where(BrandMentionDB.process_id == process_id)
        results = await session.execute(query)
        rows = results.scalars().all()
    await engine.dispose()
    return rows
