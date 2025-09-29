from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.company import Company


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, db: Session):
        super().__init__(Company, db)

    def get_by_name(self, name: str) -> Optional[Company]:
        return self.db.query(Company).filter(Company.name == name).first()
