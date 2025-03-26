from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Index, LargeBinary, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    pdf_chats = relationship("PDFChat", back_populates="user")

class PDFChat(Base):
    __tablename__ = "pdf_chats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String(255))
    pdf_content = Column(LargeBinary)
    created_at = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text, nullable=True)
    extracted_text = Column(Text, nullable=True)
    analysis = Column(JSON, nullable=True) 
    
    user = relationship("User", back_populates="pdf_chats")