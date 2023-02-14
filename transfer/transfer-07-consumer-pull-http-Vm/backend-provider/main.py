from fastapi import FastAPI
from fastapi.responses import FileResponse
import os

app = FastAPI()

file_path = "test.txt"


@app.get("/api/")
async def main():

    return FileResponse(file_path)