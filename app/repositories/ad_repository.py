from sqlalchemy.orm import Session

from app.models.ad import Ad
from app.repositories.base import BaseRepository


class AdRepository(BaseRepository[Ad]):
    def __init__(self, db: Session):
        super().__init__(Ad, db)
