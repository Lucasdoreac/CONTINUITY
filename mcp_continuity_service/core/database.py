from sqlalchemy import create_engine, Column, String, JSON, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.ext.declarative import declarative_base
from typing import List, Optional, Any, Dict
import uuid # For generating default IDs if needed, though Pydantic models expect IDs to be passed

# Import Pydantic models for type hinting and data validation in CRUD operations
from .models import Projeto as PydanticProjeto, VersaoProjeto as PydanticVersaoProjeto
from .models import Sessao as PydanticSessao
from .models import Usuario as PydanticUsuario, LicencaUsuario as PydanticLicencaUsuario

SQLALCHEMY_DATABASE_URL = "sqlite:///./mcp_continuity_service.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} # Required for SQLite for single-threaded applications
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- SQLAlchemy Table Models ---

class DBProjeto(Base):
    __tablename__ = "projetos"
    id = Column(String, primary_key=True, index=True)
    nome = Column(String, index=True)
    status = Column(String)
    contexto = Column(JSON) # For Pydantic model's 'contexto' (Dict[str, Any])
                            # JSON file storage for large contexts could be linked here in future.
    versoes = Column(JSON)  # For Pydantic model's 'versoes' (List[VersaoProjeto])

    sessoes = relationship("DBSessao", back_populates="projeto")

class DBUsuario(Base):
    __tablename__ = "usuarios"
    id = Column(String, primary_key=True, index=True)
    nome = Column(String)
    chave_criptografia = Column(String) # Store securely; consider hashing/encryption
    licenca = Column(JSON) # For Pydantic model's 'licenca' (LicencaUsuario)

    sessoes = relationship("DBSessao", back_populates="usuario")

class DBSessao(Base):
    __tablename__ = "sessoes"
    id = Column(String, primary_key=True, index=True)
    projeto_id = Column(String, ForeignKey("projetos.id"))
    usuario_id = Column(String, ForeignKey("usuarios.id"))
    estado = Column(JSON) # For Pydantic model's 'estado' (Dict[str, Any])
    ultima_atividade = Column(DateTime)

    projeto = relationship("DBProjeto", back_populates="sessoes")
    usuario = relationship("DBUsuario", back_populates="sessoes")

# --- Database Creation ---

def create_db_and_tables():
    """Creates all database tables defined by Base.metadata."""
    Base.metadata.create_all(bind=engine)

# --- Utility function to get a DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- CRUD Operations for Projeto ---

def create_projeto(db: Session, projeto: PydanticProjeto) -> DBProjeto:
    db_projeto = DBProjeto(
        id=projeto.id,
        nome=projeto.nome,
        status=projeto.status,
        contexto=projeto.contexto,
        versoes=[v.model_dump() for v in projeto.versoes] # Serialize VersaoProjeto to dict
    )
    db.add(db_projeto)
    db.commit()
    db.refresh(db_projeto)
    return db_projeto

def get_projeto_by_id(db: Session, projeto_id: str) -> Optional[DBProjeto]:
    return db.query(DBProjeto).filter(DBProjeto.id == projeto_id).first()

def get_all_projetos(db: Session, skip: int = 0, limit: int = 100) -> List[DBProjeto]:
    return db.query(DBProjeto).offset(skip).limit(limit).all()

def update_projeto(db: Session, projeto_id: str, update_data: PydanticProjeto) -> Optional[DBProjeto]:
    db_projeto = get_projeto_by_id(db, projeto_id)
    if db_projeto:
        db_projeto.nome = update_data.nome
        db_projeto.status = update_data.status
        db_projeto.contexto = update_data.contexto 
        # For 'contexto', future: consider if this should be stored in a separate JSON file
        # and only a reference/path stored in the DB.
        db_projeto.versoes = [v.model_dump() for v in update_data.versoes]
        db.commit()
        db.refresh(db_projeto)
    return db_projeto

def delete_projeto(db: Session, projeto_id: str) -> bool:
    db_projeto = get_projeto_by_id(db, projeto_id)
    if db_projeto:
        db.delete(db_projeto)
        db.commit()
        return True
    return False

# --- CRUD Operations for Usuario ---

def create_usuario(db: Session, usuario: PydanticUsuario) -> DBUsuario:
    db_usuario = DBUsuario(
        id=usuario.id,
        nome=usuario.nome,
        chave_criptografia=usuario.chave_criptografia, # Ensure this is handled securely in a real app
        licenca=usuario.licenca.model_dump() # Serialize LicencaUsuario to dict
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def get_usuario_by_id(db: Session, usuario_id: str) -> Optional[DBUsuario]:
    return db.query(DBUsuario).filter(DBUsuario.id == usuario_id).first()

def get_all_usuarios(db: Session, skip: int = 0, limit: int = 100) -> List[DBUsuario]:
    return db.query(DBUsuario).offset(skip).limit(limit).all()

def update_usuario(db: Session, usuario_id: str, update_data: PydanticUsuario) -> Optional[DBUsuario]:
    db_usuario = get_usuario_by_id(db, usuario_id)
    if db_usuario:
        db_usuario.nome = update_data.nome
        db_usuario.chave_criptografia = update_data.chave_criptografia
        db_usuario.licenca = update_data.licenca.model_dump()
        db.commit()
        db.refresh(db_usuario)
    return db_usuario

def delete_usuario(db: Session, usuario_id: str) -> bool:
    db_usuario = get_usuario_by_id(db, usuario_id)
    if db_usuario:
        db.delete(db_usuario)
        db.commit()
        return True
    return False

# --- CRUD Operations for Sessao ---

def create_sessao(db: Session, sessao: PydanticSessao) -> DBSessao:
    db_sessao = DBSessao(
        id=sessao.id,
        projeto_id=sessao.projeto_id,
        usuario_id=sessao.usuario_id,
        estado=sessao.estado,
        # For 'estado', future: ChromaDB could be used for semantic search on session states or related data.
        ultima_atividade=sessao.ultima_atividade
    )
    db.add(db_sessao)
    db.commit()
    db.refresh(db_sessao)
    return db_sessao

def get_sessao_by_id(db: Session, sessao_id: str) -> Optional[DBSessao]:
    return db.query(DBSessao).filter(DBSessao.id == sessao_id).first()

def get_all_sessoes(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    projeto_id: Optional[str] = None, 
    usuario_id: Optional[str] = None
) -> List[DBSessao]:
    query = db.query(DBSessao)
    if projeto_id:
        query = query.filter(DBSessao.projeto_id == projeto_id)
    if usuario_id:
        query = query.filter(DBSessao.usuario_id == usuario_id)
    return query.offset(skip).limit(limit).all()

def update_sessao(db: Session, sessao_id: str, update_data: PydanticSessao) -> Optional[DBSessao]:
    db_sessao = get_sessao_by_id(db, sessao_id)
    if db_sessao:
        # Only update fields that are meant to be updated: estado and ultima_atividade.
        # projeto_id and usuario_id should not be changed here.
        db_sessao.estado = update_data.estado 
        db_sessao.ultima_atividade = update_data.ultima_atividade # This is set in the router before calling
        db.commit()
        db.refresh(db_sessao)
    return db_sessao

def delete_sessao(db: Session, sessao_id: str) -> bool:
    db_sessao = get_sessao_by_id(db, sessao_id)
    if db_sessao:
        db.delete(db_sessao)
        db.commit()
        return True
    return False

# --- Placeholder for ComunicacaoMCP CRUD (if needed for persistence) ---
# class DBComunicacaoMCP(Base):
#     __tablename__ = "comunicacoes_mcp"
#     # Define columns, similar to other models
#     # ...
# def create_comunicacao_mcp(db: Session, comunicacao: PydanticComunicacaoMCP) -> DBComunicacaoMCP: ...
# etc.

# --- Placeholder for ChromaDB integration ---
# Future: Functions to interact with ChromaDB for semantic search on 'contexto' or other fields.
# def store_contexto_in_chroma(projeto_id: str, contexto: Dict[str, Any]): ...
# def search_contexto_in_chroma(query: str) -> List[str]: ... # Returns list of project_ids

# --- Placeholder for JSON file storage for large objects ---
# Future: Utility functions to save/load large JSON objects (like 'contexto') to/from files.
# def save_json_to_file(data: Dict[str, Any], file_path: str): ...
# def load_json_from_file(file_path: str) -> Dict[str, Any]: ...
# The database would then store the file path instead of the full JSON object.
