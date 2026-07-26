from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def get_local_user(db: AsyncSession) -> User:
    user = (await db.execute(select(User).where(User.username == "local"))).scalar_one_or_none()
    if user is None:
        user = User(username="local")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user
