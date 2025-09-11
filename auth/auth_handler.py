import httpx
from fastapi import HTTPException, status
from utils.logging_config import setup_logger
from core.config import settings

from utils.logging_config import setup_logger

logger = setup_logger(__name__)

# IAM validation endpoint
IAM_API_VALIDATE_URL = settings.IAM_API_VALIDATE_URL

async def validate_token_with_iam(token: str):
    """
    Validates a JWT token with the IAM API.
    Returns the user payload if valid, raises HTTPException if not.
    """
    headers = {"Authorization": f"Bearer {token}"}

    try:
        logger.info("Validating user token...")
        async with httpx.AsyncClient() as client:
            response = await client.post(IAM_API_VALIDATE_URL, headers=headers)
            if response.status_code == 200:
                logger.info("Token validated successfully")
                return response.json()
            else:
                logger.error("Token invalid or unauthorized. Try loging in.")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token invalid or unauthorized. You may need to relogin."
                )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IAM validation failed: {str(e)}")