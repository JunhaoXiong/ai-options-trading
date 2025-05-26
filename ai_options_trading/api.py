from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/summary")
def get_summary():
    return {
        "cash": 9200,
        "position_value": 800,
        "total_equity": 10000
    }

