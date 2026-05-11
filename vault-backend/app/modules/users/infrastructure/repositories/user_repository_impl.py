from typing import List, Optional

from app.modules.users.domain.entities.user import User
from app.modules.users.domain.repositories.user_repository import UserRepository
from app.modules.users.domain.datasources.user_datasource import (
    UserDatasource,
)
from app.modules.users.infrastructure.models.user_models import UserModel


class UserRepositoryImpl(UserRepository):
    def __init__(self, datasource: UserDatasource):
        self.datasource = datasource

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            username=model.username,
            public_encryption_key=model.public_encryption_key,
            public_signing_key=model.public_signing_key,
            created_at=model.created_at,
        )

    @staticmethod
    def _to_model(user: User) -> UserModel:
        return UserModel(
            id=user.id,
            email=user.email,
            username=user.username,
            public_encryption_key=user.public_encryption_key,
            public_signing_key=user.public_signing_key,
            created_at=user.created_at,
        )

    async def get_by_id(self, user_id: str) -> Optional[User]:
        model = await self.datasource.get_by_id(user_id)
        return self._to_domain(model) if model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        model = await self.datasource.get_by_email(email)
        return self._to_domain(model) if model else None

    async def save(self, user: User) -> User:
        model = self._to_model(user)
        saved = await self.datasource.save(model)
        return self._to_domain(saved)

    async def get_all(self) -> List[User]:
        models = await self.datasource.get_all()
        return [self._to_domain(m) for m in models]
