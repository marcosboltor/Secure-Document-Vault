from typing import List

from app.modules.users.domain.entities.user import User
from app.modules.users.domain.repositories.user_repository import UserRepository


class ListUsersUseCase:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def execute(self) -> List[User]:
        return await self.repository.get_all()
