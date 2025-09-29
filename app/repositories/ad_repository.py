from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.ad import Ad


class AdRepository(BaseRepository[Ad]):
    def __init__(self, db: Session):
        super().__init__(Ad, db)
