from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime, timedelta

from .. import models # models.UserCreate, models.UserResponse, models.Usuario, models.LicencaUsuario
from .. import database # database.create_usuario, database.get_usuario_by_id, database.get_all_usuarios
# Corrected import for get_db
from ..database import get_db, DBUsuario # DBUsuario for type hint

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=models.UserResponse, status_code=status.HTTP_201_CREATED)
def create_new_user(user_create: models.UserCreate, db: Session = Depends(get_db)):
    # Generate ID, crypto key, and default license
    generated_id = uuid.uuid4().hex
    generated_key = uuid.uuid4().hex # Placeholder for actual key generation
    
    # Default license: Hobby plan, valid for 1 year, active
    default_licenca = models.LicencaUsuario(
        plano="Hobby",
        validade=datetime.utcnow() + timedelta(days=365),
        ativo=True
    )
    
    full_user_data = models.Usuario(
        id=generated_id,
        nome=user_create.nome,
        chave_criptografia=generated_key,
        licenca=default_licenca
    )
    
    # The database.create_usuario function expects a Pydantic models.Usuario object
    db_user = database.create_usuario(db=db, usuario=full_user_data)
    return db_user # FastAPI will automatically handle conversion from DBUsuario to UserResponse

@router.get("/{user_id}", response_model=models.UserResponse)
def read_user(user_id: str, db: Session = Depends(get_db)):
    db_user = database.get_usuario_by_id(db, usuario_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    # The DBUsuario instance will be automatically converted to UserResponse
    # by FastAPI due to orm_mode=True (or from_attributes=True in Pydantic v2)
    # in the UserResponse schema.
    return db_user

@router.get("/", response_model=List[models.UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = database.get_all_usuarios(db, skip=skip, limit=limit)
    # Each DBUsuario instance in the list will be converted to UserResponse.
    return users
