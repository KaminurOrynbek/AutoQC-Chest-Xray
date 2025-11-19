from sqlmodel import Session, select
from typing import Type, TypeVar, Generic, List, Optional

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: Session):
        self.model = model
        self.session = session

    def get(self, id: int) -> Optional[ModelType]:
        return self.session.get(self.model, id)

    def get_all(self) -> List[ModelType]:
        return self.session.exec(select(self.model)).all()

    def create(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def update(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def delete(self, obj: ModelType):
        self.session.delete(obj)
        self.session.commit()
