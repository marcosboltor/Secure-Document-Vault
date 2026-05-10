import uuid
from datetime import datetime

from app.modules.users.domain.entities.user import User
from app.modules.users.domain.repositories.user_repository import UserRepository
from app.modules.users.exceptions.users_exceptions import UserAlreadyExistsError


class RegisterUserUseCase:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def execute(
        self,
        email: str,
        username: str,
        public_encryption_key: str,
        public_signing_key: str,
    ) -> User:
        existing = await self.repository.get_by_email(email)
        if existing:
            raise UserAlreadyExistsError(email)

        user = User(
            id=str(uuid.uuid4()),
            email=email,
            username=username,
            public_encryption_key=public_encryption_key,
            public_signing_key=public_signing_key,
            created_at=datetime.utcnow(),
        )
        return await self.repository.save(user)
