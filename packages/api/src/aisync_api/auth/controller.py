from aisync_api.server.exceptions import NotImplementedException
from .base import AuthVisitor
from .service import AuthService, SystemAuth


class AuthController(AuthVisitor):
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    async def authenticate(self, *args, **kwargs):
        self.authorize_params = args, kwargs
        return await self.auth_service.accept(self)

    async def register(self, *args, **kwargs):
        self.register_params = args, kwargs
        return await self.auth_service.accept(self)

    async def login(self, *args, **kwargs):
        self.login_params = args, kwargs
        return await self.auth_service.accept(self)

    async def visit_system_auth(self, system_auth: SystemAuth):
        if hasattr(self, "authorize_params"):
            args, kwargs = self.authorize_params
            return await system_auth.authenticate(*args, **kwargs)
        elif hasattr(self, "register_params"):
            args, kwargs = self.register_params
            return await system_auth.register(*args, **kwargs)
        elif hasattr(self, "login_params"):
            args, kwargs = self.login_params
            return await system_auth.login(*args, **kwargs)
        else:
            raise NotImplementedException(f"No implementation for {system_auth.__class__.__name__}")
