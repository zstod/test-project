from models import Users, Target, Result
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from dotenv import load_dotenv
import os

load_dotenv()

POSTGRES_NAME = os.getenv('POSTGRES_NAME')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

db_url = f'postgresql+asyncpg://{POSTGRES_NAME}:{POSTGRES_PASSWORD}@db:5432/database'
engine = create_async_engine(db_url, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def create_db_tables():
    async with engine.begin() as con:
        await con.run_sync(SQLModel.metadata.create_all)

async def start_session():
    async with async_session() as session:
        yield session
