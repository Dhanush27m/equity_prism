"""
Component: Backend -> API Layer -> Shared dependency
Belongs to: imported by every route/agent that needs "the current user" (watchlist,
portfolio, documents, document_research, snapshot.py, rag_eval.py).
Purpose: the whole app runs as a single shared local user behind the access-key gate
(see core/auth.py) rather than real multi-user accounts — this helper gets-or-creates
that one "local" user row so every other query has a user_id to scope against.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


# Returns the single local user, creating it on first call if it doesn't exist yet.
async def get_local_user(db: AsyncSession) -> User:
    user = (await db.execute(select(User).where(User.username == "local"))).scalar_one_or_none()
    if user is None:
        user = User(username="local")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user
