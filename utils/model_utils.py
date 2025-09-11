import os
import urllib.request
from fastapi import HTTPException
from urllib.parse import urlparse, unquote
from utils.logging_config import setup_logger
from core.config import settings

logger = setup_logger(__name__)

def resolve_model_path(model_reference: str, version: str) -> str:
    """
    Resolves the actual path to a model file.
    Supports both local filesystem paths and remote blob URLs.
    Downloads remote models once and caches them locally.

    Args:
        model_reference: Path or URL to the model (.keras)
        version: Model version, used for subdirectory if downloading

    Returns:
        A local path string pointing to the model file
    """
    
    logger.info(f"Beginning resolve of model path and caching for: {model_reference}")

    # Create a local versioned directory to store the downloaded model
    local_dir = os.path.join(settings.MODEL_BASE_LOCATION, version)
    os.makedirs(local_dir, exist_ok=True)
    logger.debug("Making model path locally if not exist")
 
    # Check if the model is a remote URL
    if model_reference.startswith("http"):
        # Strip URL parameters and decode filename
        parsed_url = urlparse(model_reference)
        filename = os.path.basename(parsed_url.path)
        filename = unquote(filename)
        logger.info(f"Resolved filename from URL: {filename}")

        if not filename.endswith(".keras"):
            logger.error("Downloaded model does not have a .keras extension.")
            raise HTTPException(status_code=500, detail="Invalid model format. Expected .keras file.")

        local_path = os.path.join(local_dir, filename)

        # Always remove and re-download the file
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
                logger.debug(f"Removed existing model file: {local_path}")
            except Exception as e:
                logger.warning(f"Failed to remove existing model file: {e}")

        try:
            logger.info(f"Downloading (or replacing) model from {model_reference} to {local_path}...")
            urllib.request.urlretrieve(model_reference, local_path)
            logger.info(f"Model saved successfully to {local_path}")
        except Exception as e:
            logger.error(f"Model download failed: {e}")
            raise HTTPException(status_code=500, detail=f"Could not download model from {model_reference}")

        if not os.path.isfile(local_path):
            logger.error(f"Downloaded file does not exist or is not a valid file: {local_path}")
            raise HTTPException(status_code=500, detail="Downloaded model file is invalid.")

        return local_path

    # Handle local file reference
    # If the reference is already a full path, use it directly
    if os.path.isfile(model_reference):
        return model_reference
    
    # full_local_path = os.path.join(local_dir, model_reference)
    # Otherwise, join with local_dir
    full_local_path = os.path.join(local_dir, os.path.basename(model_reference))
    logger.info(f"Resolved local model path: {full_local_path}")
    return full_local_path
