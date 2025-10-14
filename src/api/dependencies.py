from typing import Annotated
from src.infrastructure.click_house import ClickHouse
from src.infrastructure.database import DataBase
from fastapi import Depends

clickhouse_depends = Annotated[ClickHouse, Depends(ClickHouse)]
database_depends = Annotated[DataBase, Depends(DataBase)]
