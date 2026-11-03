"""HTTP request envelopes; persisted entity validation lives in validation.py."""

from pydantic import BaseModel, Field, StrictInt, StrictStr


class Login(BaseModel):
    password: str = Field(max_length=500)


class Mutation(BaseModel):
    request_id: str = Field(min_length=8, max_length=100)
    id: str = Field(min_length=1, max_length=100)
    version: int = Field(ge=0)
    action: str = "save"
    body: dict = Field(default_factory=dict)


class RewardRequestInput(BaseModel):
    request_id: str = Field(min_length=8, max_length=100)
    member_id: str
    reward_id: str


class RewardDecisionInput(BaseModel):
    request_id: str = Field(min_length=8, max_length=100)
    action: str


class PointAdjustmentInput(BaseModel):
    request_id: str = Field(min_length=8, max_length=100)
    member_id: str
    amount: int = Field(strict=True, ge=-100000, le=100000)
    reason: str = Field(default="", max_length=200)


class GamePriceInput(BaseModel):
    price: int = Field(strict=True, ge=1, le=100000)
    version: int = Field(strict=True, ge=0)


class GamePurchaseInput(GamePriceInput):
    request_id: str = Field(min_length=8, max_length=100)
    member_id: str = Field(max_length=100)


class GameActionInput(BaseModel):
    request_id: str = Field(min_length=8, max_length=100)
    version: int = Field(strict=True, ge=1)
    action: str = Field(max_length=20)
    value: StrictInt | StrictStr | None = None
