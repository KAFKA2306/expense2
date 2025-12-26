from abc import ABC, abstractmethod
from typing import List
from app.models import Transaction


class BaseScraper(ABC):
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    @abstractmethod
    async def scrape(self) -> List[Transaction]:
        pass
