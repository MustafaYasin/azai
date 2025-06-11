from pydantic.alias_generators import to_snake
from sqlalchemy.orm import declared_attr
from sqlmodel import SQLModel


class BaseSQLModel(SQLModel):
    @declared_attr
    def __tablename__(cls: type["BaseSQLModel"]) -> str:  # noqa: N805
        """Convert class name to snake case for table name."""
        return to_snake(cls.__name__)


BaseSQLModel.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_`%(constraint_name)s`",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
