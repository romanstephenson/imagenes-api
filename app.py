from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.classify_router import router as predict_router
from routers.auth_router import router as auth_router
from utils.logging_config import setup_logger
from contextlib import asynccontextmanager
from core import database as db
from core.config import settings
from utils.model_utils import resolve_model_path
from tensorflow.keras.models import load_model  # type: ignore

logger = setup_logger(__name__)
logger.info("Imagenes API initializing...")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.verify_db_connection()
    logger.info("DB Initialization complete.")

    logger.info("Resolving and loading models...")
    try:
        custom_model_path = resolve_model_path(settings.CUSTOMCNN_MODEL, settings.MODEL_VERSION)
        efficientnet_model_path = resolve_model_path(settings.EFFECIENTNETCNN_MODEL, settings.MODEL_VERSION)

        app.state.custom_model = load_model(custom_model_path)
        app.state.efficientnet_model = load_model(efficientnet_model_path)

        logger.info("Models loaded successfully.")
    except Exception as e:
        logger.exception("Failed to load models: %s", str(e))
        raise

    yield

origins = settings.ALLOWED_ORIGINS

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("Registering routes")
app.include_router(auth_router, prefix="/imagenes/auth")
app.include_router(predict_router, prefix="/imagenes")
logger.info("Routes registered")
logger.info("Imagenes app initializing completed")

# Root endpoint
@app.get("/")
def root():
    logger.info(f"{settings.APP_NAME} is running")
    return {"message": f"{settings.APP_NAME} is running"}

logger.info("FastAPI app initializing completed")
