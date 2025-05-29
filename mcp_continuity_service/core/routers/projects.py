from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from .. import models # Pydantic models: Projeto, ProjetoCreate, ProjetoResponse, ProjetoUpdate, VersaoProjeto
from .. import database # CRUD functions: create_projeto, get_all_projetos, get_projeto_by_id, update_projeto, delete_projeto
from ..database import get_db, DBProjeto # For type hinting and dependency injection

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=models.ProjetoResponse, status_code=status.HTTP_201_CREATED)
def create_new_project(project_create: models.ProjetoCreate, db: Session = Depends(get_db)):
    generated_id = uuid.uuid4().hex
    
    # Initial versoes list is empty
    full_project_data = models.Projeto(
        id=generated_id,
        nome=project_create.nome,
        status=project_create.status, # Will take default "ativo" if not provided
        contexto=project_create.contexto, # Will take default {} if not provided
        versoes=[] # Explicitly empty list for new project
    )
    
    db_project = database.create_projeto(db=db, projeto=full_project_data)
    # FastAPI handles conversion from DBProjeto to ProjetoResponse due to from_attributes = True
    return db_project

@router.get("/", response_model=List[models.ProjetoResponse])
def read_all_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    projects = database.get_all_projetos(db, skip=skip, limit=limit)
    return projects

@router.get("/{project_id}", response_model=models.ProjetoResponse)
def read_single_project(project_id: str, db: Session = Depends(get_db)):
    db_project = database.get_projeto_by_id(db, projeto_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return db_project

@router.put("/{project_id}", response_model=models.ProjetoResponse)
def update_existing_project(project_id: str, project_update: models.ProjetoUpdate, db: Session = Depends(get_db)):
    # The database.update_projeto function needs to handle Pydantic model input
    # It should fetch the project, update its fields if they are provided in project_update, and commit.
    # `versoes` are not updated here.
    
    # Convert Pydantic update model to a dictionary, excluding unset fields
    update_data_dict = project_update.model_dump(exclude_unset=True)

    # We need to ensure `update_projeto` in database.py can handle this dict or a Pydantic model.
    # The current `update_projeto` in `database.py` expects a full `PydanticProjeto`.
    # Let's adjust it or assume it's adjusted to handle partial updates.
    # For now, we'll assume the current `update_projeto` will be adapted.
    # The ideal way is to pass `project_update` directly if `database.update_projeto` is designed for it.

    # Fetch existing project to ensure it exists
    db_project = database.get_projeto_by_id(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Re-construct a full PydanticProjeto using existing data and updated fields
    # This is one way if update_projeto expects a full PydanticProjeto
    # A better way would be for update_projeto to handle partial updates directly.
    updated_project_data = models.Projeto.model_validate(db_project).model_copy(update=update_data_dict)
    
    updated_db_project = database.update_projeto(db=db, projeto_id=project_id, update_data=updated_project_data)
    
    if updated_db_project is None: # Should not happen if previous get succeeded, but good practice
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found after update attempt")
    return updated_db_project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_project(project_id: str, db: Session = Depends(get_db)):
    deleted = database.delete_projeto(db, projeto_id=project_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    # No content is returned for 204, so no explicit return value here,
    # or return a message with a different status code like 200.
    # For 204, FastAPI handles sending no body.
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Need to import Response for the delete endpoint if returning 204 with no body explicitly
from fastapi import Response
import copy # For deepcopy
from ..utils import generate_context_hash # Import the hashing utility

@router.post("/{project_id}/snapshot", response_model=models.VersaoProjeto, status_code=status.HTTP_201_CREATED)
def create_project_snapshot(project_id: str, db: Session = Depends(get_db)):
    db_project_sqla = database.get_projeto_by_id(db, projeto_id=project_id)
    if not db_project_sqla:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Ensure context is a dict for copying and hashing
    current_context = db_project_sqla.contexto if isinstance(db_project_sqla.contexto, dict) else {}

    # Create snapshot
    snapshot_context = copy.deepcopy(current_context) # Important: deep copy
    
    context_hash = generate_context_hash(snapshot_context)

    new_version = models.VersaoProjeto(
        timestamp=datetime.utcnow(),
        contexto_snapshot=snapshot_context,
        hash=context_hash
    )
    
    # Convert DBProjeto (SQLAlchemy model) to Pydantic Projeto model to easily update its 'versoes' list
    # Pydantic V2 uses model_validate instead of from_orm
    pydantic_project = models.Projeto.model_validate(db_project_sqla)
    
    # Append the new version. The 'versoes' field in pydantic_project is List[VersaoProjeto]
    pydantic_project.versoes.append(new_version)
    
    # database.update_projeto expects a Pydantic 'models.Projeto' as 'update_data'
    # This 'update_data' will contain the modified 'versoes' list.
    updated_db_project_sqla = database.update_projeto(db=db, projeto_id=project_id, update_data=pydantic_project)
    
    if not updated_db_project_sqla:
         # This case should ideally not happen if project was found initially and update_projeto is robust
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update project with new snapshot")

    return new_version
