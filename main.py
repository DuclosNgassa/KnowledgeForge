from fastapi import FastAPI
from typing import Optional

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello World"}

@app.get("/greet")
async def greet(age:int = 0, name: Optional[str] = "User") -> dict:
    return {"message": f"Hello, {name}!", "age": age}