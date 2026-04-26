from fastapi import APIRouter

router = APIRouter(prefix="/files", tags=["Vault Storage"])


@router.get("/")
async def list_files():
    return []


@router.post("/")
async def upload_file():
    return {"message": "File upload endpoint"}


@router.get("/{id}/content")
async def download_file(id: str):
    return {"message": f"Downloading content for {id}"}


@router.delete("/{id}")
async def delete_file(id: str):
    return {"message": f"Deleted {id}"}
