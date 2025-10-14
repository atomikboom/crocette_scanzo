from pydantic import BaseModel, Field
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserLogin(BaseModel):
    username: str
    password: str

class MovementIn(BaseModel):
    member_id: int
    kind: str = Field(pattern=r"^(debit|credit)$")
    crocette: int = 0
    casse: int = 0
    rule_id: int | None = None
    note: str = ""

class MemberIn(BaseModel):
    name: str

class RuleIn(BaseModel):
    title: str
    description: str = ""
    crocette: int = 0
    casse: int = 0
    active: bool = True

class MovementOut(BaseModel):
    id: int
    member_id: int
    user_id: int
    created_at: datetime
    kind: str
    crocette: int
    casse: int
    note: str
    rule_id: int | None

    class Config:
        from_attributes = True
