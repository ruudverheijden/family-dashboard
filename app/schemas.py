"""HTTP request envelopes; persisted entity validation lives in validation.py."""

from pydantic import BaseModel, Field


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
