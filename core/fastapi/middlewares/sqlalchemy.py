from uuid import uuid4

from starlette.types import ASGIApp, Receive, Scope, Send

from core.db import sessions


class SQLAlchemyMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        session_scopes = {}
        for db_type, db_session in sessions.items():
            session_id = str(uuid4())
            context = db_session.set_session_context(session_id=session_id)
            session_scopes[db_type] = context

        try:
            await self.app(scope, receive, send)
        except Exception as e:
            raise e
        finally:
            for db_type, db_session in sessions.items():
                session = db_session.session
                await session.remove()
                db_session.reset_session_context(context=session_scopes[db_type])
