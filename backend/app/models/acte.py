from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base

class Acte(Base):
    __tablename__ = "actes"
    
    # Identifiants
    numero_acte = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(String(100), nullable=False)  # ID pseudonymisé du patient
    
    # Informations cliniques
    type_acte = Column(String(200), nullable=False)
    description_clinique = Column(Text, nullable=False)
    materiel_utilise = Column(Text, nullable=True)
    duree_acte = Column(Integer, nullable=True)  # en minutes
    modificateurs = Column(JSON, nullable=True)  # Liste des modificateurs CCAM
    
    # Codage CCAM
    code_ccam_suggere = Column(String(20), nullable=True)
    code_ccam_final = Column(String(20), nullable=True)
    score_confiance = Column(Float, nullable=True)  # Score de confiance IA (0-100)
    
    # Statut et workflow
    statut = Column(String(50), default="en_attente", nullable=False)  # en_attente, valide, rejete, override
    date_validation = Column(DateTime, nullable=True)
    mode_traitement = Column(String(50), default="normal", nullable=False)  # normal, shadow, override
    
    # Métadonnées
    etablissement = Column(String(200), nullable=False)
    service = Column(String(100), nullable=True)
    date_acte = Column(DateTime, nullable=False)
    
    # Relations
    createur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    createur = relationship("Utilisateur", back_populates="actes_crees", foreign_keys=[createur_id])
    
    validateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)
    validateur = relationship("Utilisateur", foreign_keys=[validateur_id])
    
    # Relations avec autres modèles
    overrides = relationship("Override", back_populates="acte")
    audit_entries = relationship("AuditEntry", back_populates="acte")
    
    # Données blockchain
    transaction_hash = Column(String(66), nullable=True)  # Hash de la transaction blockchain
    block_number = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<Acte(id={self.id}, numero='{self.numero_acte}', statut='{self.statut}')>"