from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ActeBase(BaseModel):
    numero_acte: str = Field(..., description="Numéro unique de l'acte")
    patient_id: str = Field(..., description="ID pseudonymisé du patient")
    type_acte: str = Field(..., description="Type d'acte médical")
    description_clinique: str = Field(..., description="Description clinique détaillée")
    materiel_utilise: Optional[str] = Field(None, description="Matériel utilisé")
    duree_acte: Optional[int] = Field(None, description="Durée de l'acte en minutes")
    modificateurs: Optional[List[str]] = Field(None, description="Liste des modificateurs CCAM")
    etablissement: str = Field(..., description="Établissement de santé")
    service: Optional[str] = Field(None, description="Service médical")
    date_acte: datetime = Field(..., description="Date de réalisation de l'acte")

class ActeCreate(ActeBase):
    pass

class ActeUpdate(BaseModel):
    type_acte: Optional[str] = None
    description_clinique: Optional[str] = None
    materiel_utilise: Optional[str] = None
    duree_acte: Optional[int] = None
    modificateurs: Optional[List[str]] = None
    service: Optional[str] = None
    date_acte: Optional[datetime] = None

class ActeResponse(ActeBase):
    id: int
    code_ccam_suggere: Optional[str] = None
    code_ccam_final: Optional[str] = None
    score_confiance: Optional[float] = None
    statut: str
    date_validation: Optional[datetime] = None
    mode_traitement: str
    createur_id: int
    validateur_id: Optional[int] = None
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ActeList(BaseModel):
    actes: List[ActeResponse]
    total: int
    page: int
    size: int
    pages: int

class ActeSuggestion(BaseModel):
    acte_id: int
    suggestions: List[Dict[str, Any]] = Field(..., description="Liste des suggestions de codes CCAM")
    score_confiance: float
    explication: str
    questions: Optional[List[str]] = Field(None, description="Questions de clarification si nécessaire")

class ActeValidation(BaseModel):
    code_ccam_final: str
    justification: Optional[str] = Field(None, description="Justification de la validation")
    force_validation: bool = Field(False, description="Forcer la validation même si score faible")