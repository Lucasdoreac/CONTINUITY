from fastapi import APIRouter, HTTPException, Depends, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from .. import models # Pydantic models: Sessao, SessaoCreate, SessaoResponse, SessaoUpdate
from .. import database # CRUD functions and get_db
from ..database import get_db, DBSessao # For type hinting

router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=models.SessaoResponse, status_code=status.HTTP_201_CREATED)
def create_new_session(session_create: models.SessaoCreate, db: Session = Depends(get_db)):
    # Verify existence of project_id and usuario_id
    project = database.get_projeto_by_id(db, projeto_id=session_create.projeto_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Project with id {session_create.projeto_id} not found")
    
    user = database.get_usuario_by_id(db, usuario_id=session_create.usuario_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User with id {session_create.usuario_id} not found")

    generated_id = uuid.uuid4().hex
    current_time = datetime.utcnow()
    
    full_session_data = models.Sessao(
        id=generated_id,
        projeto_id=session_create.projeto_id,
        usuario_id=session_create.usuario_id,
        estado=session_create.estado, # Will take default {} if not provided
        ultima_atividade=current_time 
    )
    
    db_session = database.create_sessao(db=db, sessao=full_session_data)
    return db_session # FastAPI handles conversion

@router.get("/", response_model=List[models.SessaoResponse])
def read_all_sessions(
    projeto_id: Optional[str] = None, 
    usuario_id: Optional[str] = None, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    # database.get_all_sessoes will need to be updated to support these filters
    sessions = database.get_all_sessoes(db, skip=skip, limit=limit, projeto_id=projeto_id, usuario_id=usuario_id)
    return sessions

@router.get("/{session_id}", response_model=models.SessaoResponse)
def read_single_session(session_id: str, db: Session = Depends(get_db)):
    db_session = database.get_sessao_by_id(db, sessao_id=session_id)
    if db_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return db_session

@router.put("/{session_id}", response_model=models.SessaoResponse)
def update_existing_session(session_id: str, session_update: models.SessaoUpdate, db: Session = Depends(get_db)):
    db_session = database.get_sessao_by_id(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Prepare the update data Pydantic model.
    # The database.update_sessao function expects a full models.Sessao object.
    # We will construct it by taking existing values and updating where necessary.
    
    update_data_dict = session_update.model_dump(exclude_unset=True)
    
    # Create a new Pydantic model from the existing DB session, then apply updates
    # This ensures that fields not in SessaoUpdate (like projeto_id, usuario_id) are preserved.
    updated_session_data = models.Sessao.model_validate(db_session).model_copy(update=update_data_dict)
    
    # Ensure ultima_atividade is updated
    updated_session_data.ultima_atividade = datetime.utcnow()

    updated_db_session = database.update_sessao(db=db, sessao_id=session_id, update_data=updated_session_data)
    
    if updated_db_session is None: # Should not happen if previous get succeeded
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found after update attempt")
    return updated_db_session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_session(session_id: str, db: Session = Depends(get_db)):
    deleted = database.delete_sessao(db, sessao_id=session_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
