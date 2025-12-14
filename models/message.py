from __future__ import annotations
from sqlalchemy import DateTime, ForeignKey, Enum, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship 
from datetime import datetime

from db.database import Base

import enum


class SenderEnum(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class Message(Base):

    """
    messages
    --------------
    id (PK)
    conversation_id (FK -> conversations.id)
    sender         ("user" or "assistant")
    text           (full message text)
    timestamp
    """

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender: Mapped[SenderEnum] = mapped_column(Enum(SenderEnum), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    #Relationship
    conversation = relationship("Conversation", back_populates="messages")