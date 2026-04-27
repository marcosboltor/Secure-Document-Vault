from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    """Endpoint genérico para verificar que el módulo está vivo."""
    return True
