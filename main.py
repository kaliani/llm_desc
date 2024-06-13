from fastapi import FastAPI
from models import PoliticianRequest
from celery_app.app import create_politician

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
