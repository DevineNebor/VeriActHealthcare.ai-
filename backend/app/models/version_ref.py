from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON, Integer
from datetime import datetime

from .base import Base

class VersionRef(Base):
    __tablename__ = "versions_ref"
    
    # Version
    version = Column(String(20), unique=True, index=True, nullable=False)
    nom = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Métadonnées de version
    date_publication = Column(DateTime, nullable=True)
    date_effet = Column(DateTime, nullable=False)
    date_fin = Column(DateTime, nullable=True)
    
    # Statut
    is_active = Column(Boolean, default=False, nullable=False)
    is_deprecated = Column(Boolean, default=False, nullable=False)
    
    # Données de synchronisation
    source_url = Column(String(500), nullable=True)
    checksum = Column(String(64), nullable=True)  # SHA256 du fichier de référence
    metadata = Column(JSON, nullable=True)  # Métadonnées supplémentaires
    
    # Statistiques
    nombre_codes = Column(Integer, nullable=True)
    nombre_modifications = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<VersionRef(version='{self.version}', nom='{self.nom}')>"