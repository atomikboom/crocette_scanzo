from __future__ import annotations
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Text, func, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(20), default="editor")  # admin|editor|viewer
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Member(Base):
    __tablename__ = "members"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    movements: Mapped[list[Movement]] = relationship(back_populates="member", cascade="all, delete-orphan")

class Rule(Base):
    __tablename__ = "rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    crocette: Mapped[int] = mapped_column(Integer, default=0)
    casse: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Movement(Base):
    __tablename__ = "movements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    kind: Mapped[str] = mapped_column(String(10), default="debit")  # debit|credit
    note: Mapped[str] = mapped_column(String(200), default="")
    crocette: Mapped[int] = mapped_column(Integer, default=0)
    casse: Mapped[int] = mapped_column(Integer, default=0)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("rules.id"), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, default=None)


    member: Mapped[Member] = relationship(back_populates="movements")
    rule: Mapped[Rule | None] = relationship()


class BagheroneScore(Base):
    __tablename__ = "bagherone_score"
    id = Column(Integer, primary_key=True, autoincrement=True)
    giovani = Column(Integer, nullable=False, default=0)
    vecchi = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
