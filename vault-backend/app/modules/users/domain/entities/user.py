from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:

    id: str
    email: str
    username: str
    # Llave pública de cifrado X25519 (PEM) — usada para compartir archivos
    public_encryption_key: str
    # Llave pública de firma Ed25519 (PEM) — usada para verificar identidad
    public_signing_key: str
    created_at: datetime = field(default_factory=datetime.utcnow)
