from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# ------------------- Config -------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ------------------- Models -------------------
class TestCreate(BaseModel):
    name: str
    email: Optional[str] = None

class TestResponse(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ------------------- Dependencies -------------------
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# ------------------- App -------------------
app = FastAPI(title="FastAPI CRUD App")

@app.get("/")
async def root():
    return {"message": "✅ FastAPI is running and connected to PostgreSQL!"}

# CREATE
@app.post("/test/", response_model=TestResponse)
async def create_test(item: TestCreate, db: AsyncSession = Depends(get_db)):
    query = text("""
        INSERT INTO test (name, email) 
        VALUES (:name, :email) 
        RETURNING id, name, email, created_at
    """)
    result = await db.execute(query, {"name": item.name, "email": item.email})
    await db.commit()
    row = result.fetchone()
    return TestResponse.model_validate(dict(row._mapping))

# READ ALL
@app.get("/test/", response_model=List[TestResponse])
async def read_tests(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM test ORDER BY id DESC"))
    return [TestResponse.model_validate(dict(row._mapping)) for row in result.fetchall()]

# READ ONE
@app.get("/test/{item_id}", response_model=TestResponse)
async def read_test(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM test WHERE id = :id"), {"id": item_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")
    return TestResponse.model_validate(dict(row._mapping))

# UPDATE
@app.put("/test/{item_id}", response_model=TestResponse)
async def update_test(item_id: int, item: TestCreate, db: AsyncSession = Depends(get_db)):
    query = text("""
        UPDATE test SET name = :name, email = :email 
        WHERE id = :id RETURNING id, name, email, created_at
    """)
    result = await db.execute(query, {"id": item_id, "name": item.name, "email": item.email})
    await db.commit()
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")
    return TestResponse.model_validate(dict(row._mapping))

# DELETE
@app.delete("/test/{item_id}")
async def delete_test(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("DELETE FROM test WHERE id = :id RETURNING id"), {"id": item_id})
    await db.commit()
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": f"Item {item_id} deleted successfully"}