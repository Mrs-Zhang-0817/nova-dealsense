from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class Health(BaseModel):
    success: bool
    message: str

@router.get("/health")
def health() -> Health:
    return Health(success=True, message="NOVA DealSense API is running")
