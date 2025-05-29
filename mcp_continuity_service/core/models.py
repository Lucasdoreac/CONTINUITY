from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class VersaoProjeto(BaseModel):
    timestamp: datetime
    contexto_snapshot: Dict[str, Any] # objeto JSON
    hash: str

class LicencaUsuario(BaseModel):
    plano: str # Consider using an Enum for plano
    validade: datetime
    ativo: bool

class Projeto(BaseModel):
    id: str
    nome: str
    status: str # Consider using an Enum for status
    contexto: Dict[str, Any] # objeto JSON
    versoes: List[VersaoProjeto] = Field(default_factory=list)

class Sessao(BaseModel):
    id: str
    projeto_id: str
    usuario_id: str # Link to Usuario model
    estado: Dict[str, Any] # objeto JSON
    ultima_atividade: datetime

class Usuario(BaseModel):
    id: str
    nome: str
    chave_criptografia: str # Should be handled securely, not directly exposed or set by client
    licenca: LicencaUsuario

# --- User Schemas for API ---

class UserBase(BaseModel):
    nome: str

class UserCreate(UserBase):
    # For now, licenca is not part of creation, it's defaulted
    pass

class UserResponse(UserBase):
    id: str
    licenca: LicencaUsuario

    class Config:
        from_attributes = True # Updated from orm_mode = True for Pydantic v2

# --- Project Schemas for API ---

class ProjetoBase(BaseModel):
    nome: str
    status: Optional[str] = "ativo"
    contexto: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ProjetoCreate(ProjetoBase):
    pass

class ProjetoUpdate(ProjetoBase):
    # Inherits all fields from ProjetoBase, all optional by default in Pydantic V2 for updates
    # if not explicitly set as required.
    # For Pydantic V1, you'd need to make them Optional here.
    nome: Optional[str] = None
    status: Optional[str] = None
    contexto: Optional[Dict[str, Any]] = None

class ProjetoResponse(ProjetoBase):
    id: str
    versoes: List[VersaoProjeto] = Field(default_factory=list)

    class Config:
        from_attributes = True

# --- Session Schemas for API ---

class SessaoBase(BaseModel):
    projeto_id: str
    usuario_id: str
    estado: Optional[Dict[str, Any]] = Field(default_factory=dict)

class SessaoCreate(SessaoBase):
    pass

class SessaoUpdate(BaseModel): # Explicitly define fields for update
    estado: Optional[Dict[str, Any]] = None

class SessaoResponse(SessaoBase):
    id: str
    ultima_atividade: datetime

    class Config:
        from_attributes = True

class ComunicacaoMCP(BaseModel):
    cliente_id: str
    comando: str
    parametros: Dict[str, Any] # objeto JSON
    resposta: Dict[str, Any] # objeto JSON
    timestamp: datetime
