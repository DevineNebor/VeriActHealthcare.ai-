from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..core.database import get_db
from ..core.auth import get_current_user
from ..models import Utilisateur
from ..schemas.audit import AuditEntryResponse, AuditEntryList
from ..services.audit_service import AuditService
from ..services.blockchain_service import BlockchainService

router = APIRouter()

@router.get("/{acte_id}", response_model=AuditEntryList)
async def get_acte_audit_trail(
    acte_id: int,
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    action_type: Optional[str] = Query(None, description="Filtrer par type d'action"),
    date_debut: Optional[datetime] = Query(None, description="Date de début"),
    date_fin: Optional[datetime] = Query(None, description="Date de fin"),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Récupérer la trace d'audit complète d'un acte.
    
    Retourne toutes les actions effectuées sur un acte avec horodatage,
    utilisateur, et détails des changements.
    """
    audit_service = AuditService(db)
    
    # Vérifier les permissions (seul le créateur, admin ou audit peut voir l'audit)
    # TODO: Vérifier que l'utilisateur a accès à l'acte
    
    audit_entries, total = audit_service.get_acte_audit_trail(
        acte_id=acte_id,
        skip=skip,
        limit=limit,
        action_type=action_type,
        date_debut=date_debut,
        date_fin=date_fin
    )
    
    pages = (total + limit - 1) // limit
    page = (skip // limit) + 1
    
    return AuditEntryList(
        entries=audit_entries,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )

@router.get("/{acte_id}/blockchain")
async def get_blockchain_audit_trail(
    acte_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Récupérer la trace blockchain d'un acte.
    
    Retourne toutes les transactions blockchain liées à un acte,
    permettant de vérifier l'intégrité et l'immutabilité des données.
    """
    blockchain_service = BlockchainService()
    
    # Vérifier les permissions
    if current_user.role.value not in ["admin", "audit"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    try:
        blockchain_entries = await blockchain_service.get_acte_transactions(acte_id)
        return {
            "acte_id": acte_id,
            "transactions": blockchain_entries,
            "total_transactions": len(blockchain_entries)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des données blockchain: {str(e)}"
        )

@router.get("/{acte_id}/integrity")
async def verify_acte_integrity(
    acte_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Vérifier l'intégrité d'un acte.
    
    Compare les données de la base avec les données blockchain
    pour s'assurer qu'il n'y a pas eu de modification non autorisée.
    """
    audit_service = AuditService(db)
    blockchain_service = BlockchainService()
    
    # Vérifier les permissions
    if current_user.role.value not in ["admin", "audit"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    try:
        # Récupérer les données de la base
        db_data = audit_service.get_acte_current_state(acte_id)
        
        # Récupérer les données blockchain
        blockchain_data = await blockchain_service.get_acte_blockchain_state(acte_id)
        
        # Comparer les données
        integrity_check = audit_service.verify_integrity(db_data, blockchain_data)
        
        return {
            "acte_id": acte_id,
            "integrity_verified": integrity_check["verified"],
            "last_verification": datetime.utcnow(),
            "details": integrity_check["details"],
            "blockchain_consistency": integrity_check["blockchain_consistent"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la vérification d'intégrité: {str(e)}"
        )

@router.get("/overrides/summary")
async def get_overrides_summary(
    date_debut: Optional[datetime] = Query(None, description="Date de début"),
    date_fin: Optional[datetime] = Query(None, description="Date de fin"),
    etablissement: Optional[str] = Query(None, description="Filtrer par établissement"),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Récupérer un résumé des overrides.
    
    Fournit des statistiques sur les corrections manuelles effectuées,
    utile pour l'amélioration du modèle IA.
    """
    audit_service = AuditService(db)
    
    # Vérifier les permissions
    if current_user.role.value not in ["admin", "audit"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    summary = audit_service.get_overrides_summary(
        date_debut=date_debut,
        date_fin=date_fin,
        etablissement=etablissement
    )
    
    return summary

@router.get("/performance/metrics")
async def get_performance_metrics(
    date_debut: Optional[datetime] = Query(None, description="Date de début"),
    date_fin: Optional[datetime] = Query(None, description="Date de fin"),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Récupérer les métriques de performance du système.
    
    Inclut :
    - Taux d'erreur de codage
    - Nombre d'actes traités
    - Pourcentage d'actes validés sans override
    - Délai moyen de facturation
    - Score de confiance vs correction humaine
    """
    audit_service = AuditService(db)
    
    # Vérifier les permissions
    if current_user.role.value not in ["admin", "audit"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    metrics = audit_service.get_performance_metrics(
        date_debut=date_debut,
        date_fin=date_fin
    )
    
    return metrics

@router.get("/compliance/report")
async def get_compliance_report(
    date_debut: Optional[datetime] = Query(None, description="Date de début"),
    date_fin: Optional[datetime] = Query(None, description="Date de fin"),
    etablissement: Optional[str] = Query(None, description="Filtrer par établissement"),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Générer un rapport de conformité.
    
    Rapport détaillé pour les audits externes, incluant :
    - Traçabilité complète des décisions
    - Preuves blockchain
    - Conformité aux règles CCAM
    - Gestion des overrides
    """
    audit_service = AuditService(db)
    
    # Vérifier les permissions
    if current_user.role.value not in ["admin", "audit"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    report = audit_service.generate_compliance_report(
        date_debut=date_debut,
        date_fin=date_fin,
        etablissement=etablissement
    )
    
    return report