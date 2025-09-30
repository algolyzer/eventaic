from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: UUID) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        query = self.db.query(self.model)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        return query.offset(skip).limit(limit).all()

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, id: UUID, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        db_obj = self.get(id)
        if not db_obj:
            return None
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: UUID) -> bool:
        db_obj = self.get(id)
        if not db_obj:
            return False
        self.db.delete(db_obj)
        self.db.commit()
        return True
