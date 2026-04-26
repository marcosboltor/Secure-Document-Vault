from fastapi import FastAPI
from vault_backend.app.presentation.api import users, files

app = FastAPI(title="Secure Document Vault")

app.include_router(users.router)
app.include_router(files.router)

@app.get("/")
async def root():
    return {"message": "Secure Document Vault API Active"}
