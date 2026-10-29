
import os
from datetime import date, datetime

from sqlalchemy import (
    create_engine,
    String,
    Integer,
    Float,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./expenses.db",
)

engine_options = {"pool_pre_ping": True}

if DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(
        String(40), unique=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(10))
    amount: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(String(200), default="")
    transaction_date: Mapped[date] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    month: Mapped[str] = mapped_column(String(7))
    category: Mapped[str] = mapped_column(String(40))
    limit_amount: Mapped[float] = mapped_column(Float)

    __table_args__ = (
        UniqueConstraint(
            "user_id", "month", "category",
            name="unique_user_month_category",
        ),
    )


def init_db():
    Base.metadata.create_all(bind=engine)
