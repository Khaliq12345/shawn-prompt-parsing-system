from sqlmodel import Session, create_engine
from src.infrastructure.models import Output_Reports, SQLModel, Citations, Sentiments
from src.config import config


class DataBase:
    def __init__(self) -> None:
        self.engine = create_engine(
            f"postgresql+psycopg://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:5432/{config.DB_NAME}"
        )

    def create_all_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def save_citations(self, citations: list[Citations]) -> None:
        print("Saving citations")
        with Session(self.engine) as session:
            session.add_all(citations)
            session.commit()

    def save_sentiments(self, sentiments: list[Sentiments]) -> None:
        print("Saving Sentiments")
        with Session(self.engine) as session:
            session.add_all(sentiments)
            session.commit()

    def save_output_reports(self, output_report: Output_Reports) -> None:
        print("Saving Output report")
        with Session(self.engine) as session:
            session.add(output_report)
            session.commit()


# # Save a BrandMention
# async def save_brand_mention(item_lst: list[BrandDB]):
#     async_session = async_sessionmaker(engine, expire_on_commit=False)
#     async with async_session() as session:
#         for item in item_lst:
#             session.add(item)
#         await session.commit()
#
#
# # Update a LlmProcess
# async def update_llm_process_status(process_id, prompt_id, status):
#     async_session = async_sessionmaker(engine, expire_on_commit=False)
#     async with async_session() as session:
#         # create a new instance
#         if status == "running":
#             item = LlmProcess(
#                 process_id=process_id,
#                 prompt_id=prompt_id,
#                 status="running",
#                 date=datetime.now(),
#             )
#             session.add(item)
#         else:
#             # retrieve the process and update its status
#             stmt = (
#                 select(LlmProcess)
#                 .where(LlmProcess.process_id == process_id)
#                 .where(LlmProcess.prompt_id == prompt_id)
#             )
#             process = await session.scalars(stmt)
#             process = process.one()
#             process.status = status
#             process.date = datetime.now()
#         await session.commit()
#
#
# # Retrieve a process status
# async def get_llm_process_status(process_id: str, prompt_id: str):
#     engine = get_engine()
#     result = None
#     async_session = async_sessionmaker(engine, expire_on_commit=False)
#     async with async_session() as session:
#         stmt = (
#             select(LlmProcess)
#             .where(LlmProcess.process_id == process_id)
#             .where(LlmProcess.prompt_id == prompt_id)
#         )
#         process = await session.scalars(stmt)
#         process = process.one()
#         result = process.status
#     await engine.dispose()
#     return result
#
#
# # Get all BrandMention from a prompt_id
# async def get_all_brand_mentions(prompt_id: str):
#     async_session = async_sessionmaker(engine, expire_on_commit=False)
#     async with async_session() as session:
#         query = select(BrandDB).where(BrandDB.prompt_id == prompt_id)
#         results = await session.execute(query)
#         rows = results.scalars().all()
#     return rows
#
#
# # ----- Metrics -----
#
#
# # Brand Mentions
# async def get_brand_mentions_db(prompt_id: str, brand: str):
#     async_session = async_sessionmaker(engine, expire_on_commit=False)
#     mentions = []
#     async with async_session() as session:
#         # Total Mentions of Brand on this Prompt
#         stmt = (
#             select(
#                 BrandDB.date,
#                 BrandDB.process_id,
#                 func.sum(BrandDB.mention_count).label("mentions"),
#             )
#             .group_by(BrandDB.process_id, BrandDB.date)
#             .where(BrandDB.prompt_id == prompt_id, BrandDB.brand_name == brand)
#         )
#         # executing the statement
#         result = await session.execute(stmt)
#         mentions = result.mappings().all()
#     return mentions
#
#
# # Brand Share of Voice
# async def get_brand_sov_db(prompt_id: str, brand: str):
#     async_session = async_sessionmaker(engine, expire_on_commit=False)
#     sov_results = []
#     async with async_session() as session:
#         # getting the statement to calculate the share of voice
#         stmt = (
#             select(
#                 BrandDB.date,
#                 BrandDB.process_id,
#                 (
#                     func.sum(
#                         case(
#                             (
#                                 BrandDB.brand_name == brand,
#                                 BrandDB.mention_count,
#                             ),
#                             else_=0,
#                         )
#                     )
#                     * 100
#                     / func.sum(BrandDB.mention_count)
#                 ).label("sov"),
#             )
#             .where(BrandDB.prompt_id == prompt_id)
#             .group_by(BrandDB.date, BrandDB.process_id)
#         )
#         # executing statement
#         result = await session.execute(stmt)
#         sov_results = result.mappings().all()
#     return sov_results
#
#
# # Brand Coverage
# async def get_brand_coverage_db(prompt_id: str, brand: str):
#     async_session = async_sessionmaker(engine, expire_on_commit=False)
#     coverage_results = []
#     async with async_session() as session:
#         # getting the statement to calculate the coverage
#         stmt = (
#             select(
#                 BrandDB.date.label("date"),
#                 BrandDB.process_id.label("process_id"),
#                 (
#                     func.sum(case((BrandDB.brand_name == brand, 1), else_=0))
#                     * 100.0
#                     / func.count(BrandDB.id)
#                 ).label("coverage"),
#             )
#             .where(BrandDB.prompt_id == prompt_id)
#             .group_by(BrandDB.date, BrandDB.process_id)
#         )
#         # executing the statement
#         result = await session.execute(stmt)
#         coverage_results = [
#             {
#                 "date": row["date"],
#                 "process_id": row["process_id"],
#                 "coverage": round(row["coverage"] or 0, 2),
#             }
#             for row in result.mappings().all()
#         ]
#
#     return coverage_results
#
#
# # Brand Position
# async def get_brand_position_db(prompt_id: str, brand: str):
#     async_session = async_sessionmaker(engine, expire_on_commit=False)
#     avg_pos_results = []
#     async with async_session() as session:
#         # calcuating the brand position
#         stmt = (
#             select(
#                 BrandDB.date.label("date"),
#                 BrandDB.process_id.label("process_id"),
#                 (
#                     func.sum(
#                         case(
#                             (BrandDB.mention_count > 0, BrandDB.position),
#                             else_=0,
#                         )
#                     )
#                     / func.nullif(
#                         func.count(
#                             case(
#                                 (BrandDB.mention_count > 0, BrandDB.id),
#                                 else_=None,
#                             )
#                         ),
#                         0,
#                     )
#                 ).label("average_position"),
#             )
#             .where(
#                 BrandDB.prompt_id == prompt_id,
#                 BrandDB.brand_name == brand,
#             )
#             .group_by(BrandDB.date, BrandDB.process_id)
#         )
#         # executing the statement and parsing it correctly
#         result = await session.execute(stmt)
#         avg_pos_results = [
#             {
#                 "date": row["date"],
#                 "process_id": row["process_id"],
#                 "average_position": round(row["average_position"] or 0, 2),
#             }
#             for row in result.mappings().all()
#         ]
#     return avg_pos_results
#
#
# # Brand Ranking DB Function
# async def get_brand_ranking_db(prompt_id: str):
#     async_session = async_sessionmaker(engine, expire_on_commit=False)
#     async with async_session() as session:
#         # Total Mentions per Brand for this Prompt
#         stmt = (
#             select(
#                 BrandDB.brand_name,
#                 func.sum(BrandDB.mention_count),
#             )
#             .where(BrandDB.prompt_id == prompt_id)
#             .group_by(BrandDB.brand_name)
#             .order_by(func.sum(BrandDB.mention_count).desc())
#         )
#         result = await session.execute(stmt)
#         rows = result.all()
#     # Apply competition ranking
#     ranking = []
#     current_rank = 0
#     last_count = None
#     skip = 0
#     for brand, count in rows:
#         if count != last_count:
#             current_rank += 1 + skip
#             skip = 0
#         else:
#             skip += 1
#         ranking.append({"brand": brand, "mention_count": count, "rank": current_rank})
#         last_count = count
#     return ranking
