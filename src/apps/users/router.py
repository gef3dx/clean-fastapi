from fastapi import APIRouter

from .schemas.users import UserResponseSchema

from .depends import UsersUseCase

__all__ = ('router',)

router = APIRouter(prefix='/users', tags=['Users'])


@router.get('')
async def get_users(users_use_case: UsersUseCase) -> list[UserResponseSchema]:
    return await users_use_case()