from abc import ABC, abstractmethod
from typing import List, Optional

from app.modules.users.domain.entities.user import User


class UserDatasource(ABC):

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_all(self) -> List[User]:
        pass
