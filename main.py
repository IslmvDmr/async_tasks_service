
import uvicorn
from fastapi import FastAPI

from app.packages.configs import settings
from app.routers.tasks import router

app = FastAPI(title=settings.APP_NAME)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host=settings.APP_HOST, port=settings.APP_PORT)