"""Sample FastAPI app, factory functions, and Pydantic models for comprehensive testing."""

from fastapi import APIRouter, FastAPI, WebSocket
from pydantic import BaseModel, Field


class Item(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: float = Field(gt=0, description="The price must be greater than zero")


class User(BaseModel):
    username: str
    email: str
    items: list[Item] = []


app = FastAPI(title="Sample Test App", version="1.0.0")

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/", response_model=list[User], summary="List all users", operation_id="list_users"
)
def get_users() -> list[User]:
    users: list[User] = []
    return users


@router.post(
    "/", response_model=User, summary="Create a user", operation_id="create_user"
)
def create_user(user: User) -> User:
    return user


@app.get("/health", summary="Health check endpoint")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_text("Hello")
    await websocket.close()


def make_app() -> FastAPI:
    """Factory function returning a configured FastAPI instance."""
    factory_app = FastAPI(title="Factory Created App", version="2.0.0")

    @factory_app.get("/factory-route")
    def factory_route() -> dict[str, str]:
        return {"msg": "from factory"}

    _ = factory_route

    return factory_app


app.include_router(router)
