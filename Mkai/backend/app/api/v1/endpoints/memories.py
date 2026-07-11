from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.memory_service import MemoryService

router = APIRouter()


@router.get("")
def list_memories(user_id: str = "muhammed", db: Session = Depends(get_db)) -> list[dict]:
    return [item.to_dict() for item in MemoryService(db).list_memories(user_id)]


@router.patch("/{memory_id}")
def update_memory(memory_id: int, value: str | None = None, category: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    updated = MemoryService(db).update_memory(memory_id, value=value, category=category)
    return {"status": "updated", "memory": updated.to_dict() if updated else None}


@router.delete("/{memory_id}")
def delete_memory(memory_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    MemoryService(db).delete_memory(memory_id)
    return {"status": "deleted"}
