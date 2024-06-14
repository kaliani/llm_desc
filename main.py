import os

from dotenv import load_dotenv
from fastapi import FastAPI

from celery_app.app import create_politician
from models import PoliticianRequest

load_dotenv()

app = FastAPI()


@app.post("/generate_politician/")
def generate_politician_card(request: PoliticianRequest):
    create_politician.delay(request.name, request.wikidataid)
    return {"Message": "OK"}


@app.get("/health/", tags=["Health Check"])
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host=host, port=port)
