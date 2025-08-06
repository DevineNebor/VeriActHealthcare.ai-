from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship

from .base import Base

class Override(Base):
    __tablename__ = "overrides"
    
    # Relations
    acte_id = Column(Integer, ForeignKey("actes.id"), nullable=False)
    acte = relationship("Acte", back_populates="overrides")
    
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    utilisateur = relationship("Utilisateur", back_populates="overrides")
    
    # Données de l'override
    code_ccam_original = Column(String(20), nullable=False)
    code_ccam_override = Column(String(20), nullable=False)
    justification = Column(Text, nullable=False)
    
    # Métadonnées
    type_override = Column(String(50), nullable=False)  # correction, precision, modificateur
    signature_numerique = Column(String(255), nullable=True)  # Signature de l'utilisateur
    metadata = Column(JSON, nullable=True)  # Données supplémentaires
    
    # Validation
    is_approved = Column(Boolean, default=False, nullable=False)
    approved_by = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)
    approver = relationship("Utilisateur", foreign_keys=[approved_by])
    
    # Blockchain
    transaction_hash = Column(String(66), nullable=True)
    
    def __repr__(self):
        return f"<Override(id={self.id}, acte_id={self.acte_id}, type='{self.type_override}')>"