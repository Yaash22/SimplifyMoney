from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    chat_id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class ChatBase(BaseModel):
    conversation_id: str

class ChatCreate(ChatBase):
    user_id: int

class Chat(ChatBase):
    id: int
    created_at: datetime
    summary: Optional[str] = None
    messages: List[Message] = []

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    chats: List[Chat] = []
    pdf_chats: List['PDFChat'] = []

    class Config:
        orm_mode = True

class PDFChatBase(BaseModel):
    filename: str

class PDFChatCreate(PDFChatBase):
    user_id: int

class PDFChat(PDFChatBase):
    id: int
    created_at: datetime
    summary: Optional[str] = None
    extracted_text: Optional[str] = None
    analysis: Optional[Dict] = None

    class Config:
        orm_mode = True