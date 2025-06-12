import datetime

from sqlalchemy import func
from sqlmodel import Field

from database.base import BaseSQLModel


class TimestampMixin(BaseSQLModel):
    created_at: datetime.datetime = Field(nullable=False, sa_column_kwargs={"server_default": func.now()})
    updated_at: datetime.datetime = Field(
        nullable=False, sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()}
    )
