from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base

class AuditEntry(Base):
    __tablename__ = "audit_entries"
    
    # Relations
    acte_id = Column(Integer, ForeignKey("actes.id"), nullable=True)
    acte = relationship("Acte", back_populates="audit_entries")
    
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=True)
    utilisateur = relationship("Utilisateur", back_populates="audit_entries")
    
    # Données d'audit
    action = Column(String(100), nullable=False)  # create, update, validate, override, etc.
    entity_type = Column(String(50), nullable=False)  # acte, override, code_ccam, etc.
    entity_id = Column(Integer, nullable=True)
    
    # Changements
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # Métadonnées
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(100), nullable=True)
    
    # Blockchain
    transaction_hash = Column(String(66), nullable=True)
    block_number = Column(Integer, nullable=True)
    
    # Horodatage précis
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AuditEntry(id={self.id}, action='{self.action}', entity_type='{self.entity_type}')>"