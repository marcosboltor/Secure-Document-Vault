from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class User:
    id: str
    name: str
    email: str
    public_key_encryption: str
    public_key_signing: str


@dataclass
class VaultFile:
    id: str
    name: str
    owner_id: str
    recipients: List[str]
    created_at: datetime
    size: int
    signer_public_key: str
    vault_path: str
