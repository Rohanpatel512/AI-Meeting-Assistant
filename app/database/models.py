from sqlalchemy import ForeignKey
from sqlalchemy import String 
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column 

class Base(DeclarativeBase):
    pass 


class User(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)

class Usage(Base):
    __tablename__ = "usage"

    usage_id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id",  ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    total_file_size: Mapped[float] = mapped_column(nullable=True)
    summary_amount: Mapped[int] = mapped_column(nullable=True)


