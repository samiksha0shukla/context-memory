from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, Integer, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.contextmemory.db.database import Base

class Conversation(Base):
    """
    conversations
    -------------
    id (PK)
    created_at
    updated_at
    """

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))

    #Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    summary = relationship("ConversationSummary", back_populates="conversation", uselist=False, cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="conversation", cascade="all, delete-orphan")

