from fastapi import APIRouter

from app.services.provider_service import ProviderService

router = APIRouter()


@router.get("", response_model=dict)
def list_providers() -> dict:
    return ProviderService().get_provider_status()
