from sqlalchemy import Column, String, Boolean, Enum, Text
from sqlalchemy.orm import relationship
import enum

from .base import Base

class UserRole(enum.Enum):
    MEDECIN = "medecin"
    ADMINISTRATIF = "administratif"
    ADMIN = "admin"
    AUDIT = "audit"

class Utilisateur(Base):
    __tablename__ = "utilisateurs"
    
    # Identifiants
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Informations personnelles
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    specialite = Column(String(100), nullable=True)
    etablissement = Column(String(200), nullable=True)
    
    # Rôles et permissions
    role = Column(Enum(UserRole), default=UserRole.ADMINISTRATIF, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Métadonnées
    signature_key = Column(String(255), nullable=True)  # Clé pour signature numérique
    preferences = Column(Text, nullable=True)  # JSON des préférences utilisateur
    
    # Relations
    actes_crees = relationship("Acte", back_populates="createur", foreign_keys="Acte.createur_id")
    overrides = relationship("Override", back_populates="utilisateur")
    audit_entries = relationship("AuditEntry", back_populates="utilisateur")
    
    def __repr__(self):
        return f"<Utilisateur(id={self.id}, email='{self.email}', role='{self.role.value}')>"