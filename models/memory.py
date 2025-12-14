from __future__ import annotations
from typing import Optional, Dict, List
from datetime import datetime
from sqlalchemy import Text, Integer, DateTime, ForeignKey, String, text
from sqlalchemy import JSON as JSONType

from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base

class Memory(Base):
    """
    memories
    ----------------------
    id (PK)
    conversation_id (FK -> conversations.id)
    text            (the memory fact)
    category        (optional: "preference", "profile", "hobby", etc.)
    embedding       (vector)
    metadata        (JSON: timestamps, tags, source message IDs)
    created_at
    updated_at
    """

    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    memory_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    embedding: Mapped[List[float]] = mapped_column(JSONType, nullable=True)
    memory_metadata: Mapped[Optional[Dict]] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))

    #Relationship
    conversation = relationship("Conversation", back_populates="memory")