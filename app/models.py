from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class TransactionBase(SQLModel):
    date: datetime
    description: str
    amount: float
    category: Optional[str] = None
    source: str
    currency: str = "JPY"


class Transaction(TransactionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TransactionCreate(TransactionBase):
    pass


class Asset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    balance: float
    updated_at: datetime = Field(default_factory=datetime.utcnow)
