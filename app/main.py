from fastapi import FastAPI, WebSocket, UploadFile, File, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import asyncio
import PyPDF2
import io
from fastapi.responses import JSONResponse

from .database import get_db, create_tables
from . import models, schemas
from .summarizer import summarize_conversation

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await create_tables()

@app.post("/users/", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    try:
       
        query = select(models.User).where(models.User.email == user.email)
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            return JSONResponse(
                status_code=400,
                content={"detail": f"User with email {user.email} already exists"}
            )
        
      
        query = select(models.User).where(models.User.username == user.username)
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            return JSONResponse(
                status_code=400,
                content={"detail": f"User with username {user.username} already exists"}
            )
        

        db_user = models.User(**user.dict())
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return JSONResponse(
            status_code=200,
            content={
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email
            }
        )
    except Exception as e:
        print(f"Error creating user: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error creating user: {str(e)}"}
        )

@app.delete("/users/{email}")
async def delete_user(email: str, db: AsyncSession = Depends(get_db)):
    query = select(models.User).where(models.User.email == email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    return {"message": "User deleted successfully"}

@app.post("/chats/", response_model=schemas.Chat)
async def create_chat(chat: schemas.ChatCreate, db: AsyncSession = Depends(get_db)):
    db_chat = models.Chat(**chat.dict())
    db.add(db_chat)
    await db.commit()
    await db.refresh(db_chat)
    return db_chat

@app.post("/chats/{chat_id}/messages/", response_model=schemas.Message)
async def create_message(chat_id: int, message: schemas.MessageCreate, db: AsyncSession = Depends(get_db)):
    db_message = models.Message(**message.dict(), chat_id=chat_id)
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message

@app.get("/chats/{conversation_id}", response_model=schemas.Chat)
async def get_chat(conversation_id: str, db: AsyncSession = Depends(get_db)):
    query = select(models.Chat).where(models.Chat.conversation_id == conversation_id)
    result = await db.execute(query)
    chat = result.scalar_one_or_none()
    
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

@app.post("/chats/summarize/{conversation_id}")
async def summarize_chat(conversation_id: str, db: AsyncSession = Depends(get_db)):
    query = select(models.Chat).where(models.Chat.conversation_id == conversation_id)
    result = await db.execute(query)
    chat = result.scalar_one_or_none()
    
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = [msg.content for msg in chat.messages]
    summary = await summarize_conversation(messages)
    
    chat.summary = summary
    await db.commit()
    return {"summary": summary}

@app.get("/users/{user_id}/chats", response_model=List[schemas.Chat])
async def get_user_chats(
    user_id: int, 
    page: int = 1, 
    limit: int = 10, 
    db: AsyncSession = Depends(get_db)
):
    skip = (page - 1) * limit
    query = select(models.Chat).where(models.Chat.user_id == user_id).offset(skip).limit(limit)
    result = await db.execute(query)
    chats = result.scalars().all()
    return chats

@app.delete("/chats/{conversation_id}")
async def delete_chat(conversation_id: str, db: AsyncSession = Depends(get_db)):
    query = select(models.Chat).where(models.Chat.conversation_id == conversation_id)
    result = await db.execute(query)
    chat = result.scalar_one_or_none()
    
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    await db.delete(chat)
    await db.commit()
    return {"message": "Chat deleted successfully"}

@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            summary = await summarize_conversation([data])
            await websocket.send_text(summary)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.post("/pdf-chats/upload/", response_model=schemas.PDFChat)
async def upload_pdf_chat(
    file: UploadFile = File(...),
    user_id: int = Query(..., description="The ID of the user uploading the PDF"),
    db: AsyncSession = Depends(get_db)
):
    try:
        user_query = select(models.User).where(models.User.id == user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
            
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        pdf_content = await file.read()

        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        extracted_text = ""
        for page in pdf_reader.pages:
            extracted_text += page.extract_text() + "\n"
        
        print(f"Extracted text length: {len(extracted_text)}")

        db_pdf_chat = models.PDFChat(
            user_id=user_id,
            filename=file.filename,
            pdf_content=pdf_content,
            extracted_text=extracted_text
        )
        db.add(db_pdf_chat)
        await db.commit()
        await db.refresh(db_pdf_chat)
        
        print(f"Created PDF chat with ID: {db_pdf_chat.id} for user: {user_id}")
        return db_pdf_chat
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pdf-chats/{chat_id}/summarize/")
async def summarize_pdf_chat(chat_id: int, db: AsyncSession = Depends(get_db)):
    query = select(models.PDFChat).where(models.PDFChat.id == chat_id)
    result = await db.execute(query)
    pdf_chat = result.scalar_one_or_none()
    
    if pdf_chat is None:
        raise HTTPException(status_code=404, detail="PDF chat not found")

    text_chunks = [pdf_chat.extracted_text[i:i+1000] for i in range(0, len(pdf_chat.extracted_text), 1000)]
    summaries = []
    sentiments = []
    participants = set()
    
    for chunk in text_chunks:
        analysis = await summarize_conversation([chunk])
        summaries.append(analysis["summary"])
        sentiments.append(analysis["sentiment"])
        participants.update(analysis["participants"])
    
    final_summary = "\n".join(summaries)
    overall_sentiment = max(set(sentiments), key=sentiments.count)

    pdf_chat.summary = final_summary
    pdf_chat.analysis = {
        "sentiment": overall_sentiment,
        "participants": list(participants),
        "message_count": len(text_chunks)
    }
    await db.commit()
    
    return {
        "summary": final_summary,
        "sentiment": overall_sentiment,
        "participants": list(participants),
        "message_count": len(text_chunks)
    }

@app.get("/users/{user_id}/pdf-chats", response_model=List[schemas.PDFChat])
async def get_user_pdf_chats(
    user_id: int, 
    page: int = 1, 
    limit: int = 10, 
    db: AsyncSession = Depends(get_db)
):
    try:
        print(f"Fetching PDF chats for user_id: {user_id}")
        skip = (page - 1) * limit
        query = select(models.PDFChat).where(models.PDFChat.user_id == user_id).offset(skip).limit(limit)
        result = await db.execute(query)
        pdf_chats = result.scalars().all()
        print(f"Found {len(pdf_chats)} PDF chats")
        return pdf_chats
    except Exception as e:
        print(f"Error fetching PDF chats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pdf-chats/{chat_id}", response_model=schemas.PDFChat)
async def get_pdf_chat(chat_id: int, db: AsyncSession = Depends(get_db)):
    query = select(models.PDFChat).where(models.PDFChat.id == chat_id)
    result = await db.execute(query)
    pdf_chat = result.scalar_one_or_none()
    
    if pdf_chat is None:
        raise HTTPException(status_code=404, detail="PDF chat not found")
    return pdf_chat

@app.delete("/pdf-chats/{chat_id}")
async def delete_pdf_chat(chat_id: int, db: AsyncSession = Depends(get_db)):
    query = select(models.PDFChat).where(models.PDFChat.id == chat_id)
    result = await db.execute(query)
    pdf_chat = result.scalar_one_or_none()
    
    if pdf_chat is None:
        raise HTTPException(status_code=404, detail="PDF chat not found")
    
    await db.delete(pdf_chat)
    await db.commit()
    return {"message": "PDF chat deleted successfully"}