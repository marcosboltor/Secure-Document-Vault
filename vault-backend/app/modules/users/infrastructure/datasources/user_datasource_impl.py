from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.users.domain.datasources.user_datasource import (
    UserDatasource,
)
from app.modules.users.infrastructure.models.user_models import UserModel


class UserDatasourceImpl(UserDatasource):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: str) -> Optional[UserModel]:
        result = await self.session.exec(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.first()

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        result = await self.session.exec(
            select(UserModel).where(UserModel.email == email)
        )
        return result.first()

    async def save(self, model: UserModel) -> UserModel:
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model

    async def get_all(self) -> List[UserModel]:
        result = await self.session.exec(select(UserModel))
        return list(result.all())
