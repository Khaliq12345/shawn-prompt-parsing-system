from typing import Annotated
from src.infrastructure.database import DataBase
from fastapi import Depends

database_depends = Annotated[DataBase, Depends(DataBase)]
