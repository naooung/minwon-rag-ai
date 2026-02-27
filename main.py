import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)

from app.api.routes import router
from app.llm.qwen import qwen_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    qwen_model.load()
    yield


app = FastAPI(title="minwon-rag-ai", lifespan=lifespan)
app.include_router(router)
