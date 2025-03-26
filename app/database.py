from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

os.makedirs(os.path.dirname("./chat_app.db"), exist_ok=True)

DATABASE_URL = "sqlite+aiosqlite:///./chat_app.db"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def create_tables():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)  
            await conn.run_sync(Base.metadata.create_all) 
            print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise