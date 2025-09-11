from datetime import datetime, timezone
import io
from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends, Request
from auth.dependencies import get_current_user
from core.config import settings
from fastapi.security import OAuth2PasswordBearer
from entity.cancer_model import CancerInput, CancerRecord
# from tensorflow.keras.models import load_model  # type: ignore
from PIL import Image
import numpy as np
import pydicom
from utils.logging_config import setup_logger
from core.config import settings
import utils.model_utils as mutil

logger = setup_logger(__name__)

router = APIRouter()
# JWT dependency
# It's used only for API docs to show where a token can be obtained
oauth2_scheme = OAuth2PasswordBearer(settings.TOKEN_URL)

model_version = settings.MODEL_VERSION

@router.post("/classify", response_model=CancerInput)
async def predict(request: Request, file: UploadFile = File(...), user=Depends(get_current_user)):

    model = request.app.state.custom_model

    logger.info(f"Model input shape: {model.input_shape}")

    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
    
        image_data = await file.read()

        image = Image.open(io.BytesIO(image_data)).convert("L")  # Convert to grayscale

        if image.size != (512, 512):
            logger.warning(f"Resizing image from {image.size} to (512, 512)")
            image = image.resize((512, 512))

        if file.size is not None and file.size < 10240:  # 10 KB
            raise HTTPException(status_code=400, detail="Image file too small to be valid.")


        processed = np.asarray(image) / 255.0  # Normalize image to [0, 1]
        processed = np.expand_dims(processed, axis=-1)  # (512, 512, 1)
        pred = model.predict(np.expand_dims(processed, axis=0))[0]  # (1, 1)

        label = "cancer" if pred[0] > 0.5 else "not_cancer"
        confidence = round(float(pred[0]), 3)

        logger.info(f"User={user['username']} | IP={request.client.host} | DICOM={file.filename} | Prediction={label}, Confidence={confidence}")

        await CancerRecord.create_cancer_prediction(
            metadata={
                "filename": file.filename, 
                "model_type": "Custom CNN"
                },
            username=user["username"],
            prediction=label,
            confidence=confidence,
            cnn_model_version=model_version,
            company_id=user.get("company_id")
        )

        return {
            "cnn_model_type": "Custom CNN",
            "prediction": label,
            "confidence": round(float(pred[0]), 3),
            "filename": file.filename,
            "cnn_model_version": model_version,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise    
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/classify/dcm")
async def predict_from_dicom(request: Request, file: UploadFile = File(...), user=Depends(get_current_user)):

    model = request.app.state.custom_model

    if not file.filename.endswith(".dcm"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a DICOM (.dcm) file")

    try:
        # Read the DICOM file
        dcm_bytes = await file.read()
        ds = pydicom.dcmread(io.BytesIO(dcm_bytes))

         # Validate modality
        modality = getattr(ds, "Modality", None)
        if modality != "MR":
            logger.warning(f"Rejected DICOM with unsupported Modality: {modality}")
            raise HTTPException(status_code=400, detail="Only MR modality DICOMs are supported.")

        # Extract pixel array and convert to PIL image
        pixel_array = ds.pixel_array.astype(np.float32)
        pixel_array -= pixel_array.min()
        pixel_array /= pixel_array.max() if pixel_array.max() != 0 else 1

        image = Image.fromarray((pixel_array * 255).astype(np.uint8)).convert("L")

        if image.size != (512, 512):
            logger.warning(f"Resizing DICOM image from {image.size} to (512, 512)")
            image = image.resize((512, 512))

        processed = np.asarray(image) / 255.0
        processed = np.expand_dims(processed, axis=-1)
        pred = model.predict(np.expand_dims(processed, axis=0))[0]

        label = "cancer" if pred[0] > 0.5 else "not_cancer"
        confidence = round(float(pred[0]), 3)

        logger.info(f"User={user['username']} | IP={request.client.host} | DICOM={file.filename} | Prediction={label}, Confidence={confidence}")

        await CancerRecord.create_cancer_prediction(
            metadata={
            "filename": file.filename, 
            "model_type": "Custom CNN", 
            "modality": modality
            },
            username=user["username"],
            prediction=label,
            confidence=confidence,
            cnn_model_version=model_version,
            company_id=user.get("company_id")
        )

        return {
            "cnn_model_type": "Custom CNN",
            "prediction": label,
            "confidence": round(float(pred[0]), 3),
            "filename": file.filename,
            "cnn_model_version": model_version,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DICOM prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process DICOM file: {str(e)}")


@router.post("/classify/rgb", response_model=CancerInput)
async def predict_rgb(request: Request, file: UploadFile = File(...), user=Depends(get_current_user)):

    eNetTLearningModel = request.app.state.efficientnet_model

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data)).convert("RGB")  # Convert to 3-channel RGB

        if image.size != (512, 512):
            logger.warning(f"Resizing image from {image.size} to (512, 512)")
            image = image.resize((512, 512))

        processed = np.asarray(image) / 255.0  # Normalize
        processed = np.expand_dims(processed, axis=0)  # shape (1, 512, 512, 3)

        pred = eNetTLearningModel.predict(processed)[0]
        label = "cancer" if pred[0] > 0.5 else "not_cancer"
        confidence = round(float(pred[0]), 3)

        logger.info(f"User={user['username']} | IP={request.client.host} | File={file.filename} | Prediction={label}, Confidence={confidence}")

        await CancerRecord.create_cancer_prediction(
            metadata={
                "filename": file.filename, 
                "model_type": "EfficientNetB0"
                },
            username=user["username"],
            prediction=label,
            confidence=confidence,
            cnn_model_version=model_version,
            company_id=user.get("company_id")
        )

        return {
            "cnn_model_type": "Custom CNN",
            "prediction": label,
            "confidence": round(float(pred[0]), 3),
            "filename": file.filename,
            "cnn_model_version": model_version,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RGB Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail="Prediction failed")


@router.get("/metatlearningenet")
def get_model_meta_tlearning_enetB0(request: Request, user=Depends(get_current_user)):

    eNetTLearningModel = request.app.state.efficientnet_model

    logger.info("/v1/metatlearningenet accessed")

    try:
        return {
            "model_name": "BreastCancerCNN_EfficientNet",
            "version": "1.0",
            "model_version": settings.MODEL_VERSION,
            "input_format": "image/jpeg, image/png",
            "input_shape": eNetTLearningModel.input_shape,
            "output": ["cancer", "not_cancer"]#,
            # "model_path": model_path
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve model metadata: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Metadata unavailable: {str(e)} ")
    


@router.get("/metacustom")
def get_model_meta_custom(request: Request,):

    model = request.app.state.custom_model

    logger.info("/meta accessed")

    try:
        return {
            "model_name": "BreastCancerCNN_model",
            "version": "1.0",
            "model_version": settings.MODEL_VERSION,
            "input_format": "image/jpeg, image/png",
            "input_shape": model.input_shape,
            "output": ["cancer", "not_cancer"]#,
            # "model_path": model_path
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve model metadata: %s", str(e))
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Metadata unavailable")
