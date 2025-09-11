from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from core.database import db

class CancerInput(BaseModel):
    cnn_model_type: str
    prediction: str
    confidence: float
    filename: str
    cnn_model_version: str
    timestamp: str

class CancerRecord(BaseModel):
    id: Optional[str]
    username: str
    metadata: Dict[str, Any]
    prediction: str
    confidence: float
    cnn_model_version: str
    timestamp: datetime
    company_id: Optional[str] = None

    @staticmethod
    async def create_cancer_prediction(
        metadata: Dict[str, Any], 
        username: str, 
        prediction: str, 
        confidence: float, 
        cnn_model_version: str, 
        company_id: Optional[str] = None
        ) -> str:

        record = {
            "username": username,
            "metadata": metadata,
            "prediction": prediction,
            "confidence": confidence,
            "model_version": cnn_model_version,
            "timestamp": datetime.now(timezone.utc),
        }

        if company_id:
            record["company_id"] = company_id

        result = await db["image_predictions"].insert_one(record)
        
        return str(result.inserted_id)

    @staticmethod
    async def get_cancer_predictions(username: str, company_id: Optional[str] = None, limit: int = 100 ) -> List["CancerRecord"]:

        query = {"username": username}
        if company_id:
            query["company_id"] = company_id

        cursor = db["image_predictions"].find(query).sort("timestamp", -1).limit(limit)
        records = []
        async for doc in cursor:
            record = CancerRecord(
                id=str(doc["_id"]),
                username=doc["username"],
                metadata=doc["metadata"],
                prediction=doc["prediction"],
                confidence=doc["confidence"],
                cnn_model_version=doc["model_version"],
                timestamp=doc["timestamp"],
                company_id=doc.get("company_id")
            )
            records.append(record)

        return records
