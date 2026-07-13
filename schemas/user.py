from pydantic import BaseModel


class UserOut(BaseModel):
    id: str
    name: str
    avatar: str
    role: str
    online: bool

    model_config = {"from_attributes": True}
