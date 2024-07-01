from fastapi import FastAPI, HTTPException
from typing import List
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from fastapi.middleware.cors import CORSMiddleware
from models import Base, Todo
from schemas import TodoCreate, TodoUpdate, TodoResponse

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

app = FastAPI()

# Настройка CORS (для тестирования)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка базы данных
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# Инициализация базы данных
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("startup")
async def on_startup():
    await init_db()


@app.post("/todos", response_model=TodoResponse, status_code=201)
async def create_todo(todo: TodoCreate):
    async with SessionLocal() as session:
        new_todo = Todo(
            title=todo.title,
            description=todo.description
        )
        session.add(new_todo)
        await session.commit()
        await session.refresh(new_todo)
        return new_todo


@app.get("/todos/{todo_id}", response_model=TodoResponse)
async def read_todo(todo_id: int):
    async with SessionLocal() as session:
        stmt = select(Todo).filter(Todo.id == todo_id)
        result = await session.execute(stmt)
        todo = result.scalars().first()
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        return todo


@app.put("/todos/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: int, todo_update: TodoUpdate):
    async with SessionLocal() as session:
        stmt = select(Todo).filter(Todo.id == todo_id)
        result = await session.execute(stmt)
        todo = result.scalars().first()
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")

        todo.title = todo_update.title
        todo.description = todo_update.description
        todo.completed = todo_update.completed

        session.add(todo)
        await session.commit()
        await session.refresh(todo)
        return todo


@app.delete("/todos/{todo_id}", status_code=204)
async def delete_todo(todo_id: int):
    async with SessionLocal() as session:
        stmt = select(Todo).filter(Todo.id == todo_id)
        result = await session.execute(stmt)
        todo = result.scalars().first()
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")

        await session.delete(todo)
        await session.commit()
        return {"detail": "Todo successfully deleted"}
