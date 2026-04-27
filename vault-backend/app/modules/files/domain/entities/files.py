from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class VaultFile:
    id: str
    name: str
    owner_id: str
    owner_name: str
    recipients: List[str]  # Lista de IDs de usuarios con acceso
    created_at: datetime
    signer_public_key_base64: str
    encrypted_content: Optional[bytes] = None
    
    def is_owner(self, user_id: str) -> bool:
        return self.owner_id == user_id
    
    def has_access(self, user_id: str) -> bool:
        return self.is_owner(user_id) or user_id in self.recipients
