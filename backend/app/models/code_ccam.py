from sqlalchemy import Column, String, Text, Boolean, JSON, Float, Integer
from sqlalchemy.orm import relationship

from .base import Base

class CodeCCAM(Base):
    __tablename__ = "codes_ccam"
    
    # Code CCAM
    code = Column(String(20), unique=True, index=True, nullable=False)
    libelle = Column(Text, nullable=False)
    
    # Classification
    chapitre = Column(String(10), nullable=True)
    section = Column(String(10), nullable=True)
    sous_section = Column(String(10), nullable=True)
    
    # Informations tarifaires
    tarif_base = Column(Float, nullable=True)
    tarif_ambulatoire = Column(Float, nullable=True)
    tarif_hospitalier = Column(Float, nullable=True)
    
    # Modificateurs et contraintes
    modificateurs_compatibles = Column(JSON, nullable=True)  # Liste des modificateurs autorisés
    modificateurs_incompatibles = Column(JSON, nullable=True)  # Liste des modificateurs interdits
    contraintes = Column(JSON, nullable=True)  # Règles métier spécifiques
    
    # Métadonnées
    version_ccam = Column(String(20), nullable=False)  # Version du référentiel CCAM
    date_effet = Column(String(10), nullable=True)  # Date d'effet du code
    date_fin = Column(String(10), nullable=True)  # Date de fin de validité
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relations avec les actes
    actes_suggere = relationship("Acte", foreign_keys="Acte.code_ccam_suggere")
    actes_final = relationship("Acte", foreign_keys="Acte.code_ccam_final")
    
    def __repr__(self):
        return f"<CodeCCAM(code='{self.code}', libelle='{self.libelle[:50]}...')>"