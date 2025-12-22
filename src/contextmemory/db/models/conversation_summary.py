from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, Text, DateTime, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from contextmemory.db.database import Base

class ConversationSummary(Base):
    """
    conversation_summary
    -----------------------
    id (PK)
    conversation_id (FK -> conversations.id)
    summary_text   (compressed summary)
    updated_at
    """

    __tablename__ = "conversation_summary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))

    #Relationship
    conversation = relationship("Conversation", back_populates="summary")