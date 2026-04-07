from fastapi import FastAPI

from app.api.routes import router
from app.jobs.scheduler import start_scheduler

app = FastAPI(title="FII Asymmetry API", version="0.1.0")
app.include_router(router)


@app.on_event("startup")
def on_startup() -> None:
    start_scheduler()
