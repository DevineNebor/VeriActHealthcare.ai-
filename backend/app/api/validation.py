from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..core.auth import get_current_user
from ..models import Utilisateur
from ..schemas.acte import ActeValidation
from ..schemas.override import OverrideCreate, OverrideResponse
from ..services.acte_service import ActeService
from ..services.blockchain_service import BlockchainService
from ..services.override_service import OverrideService

router = APIRouter()

@router.post("/{acte_id}", response_model=dict)
async def validate_acte(
    acte_id: int,
    validation_data: ActeValidation,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Valider un acte avec un code CCAM final.
    
    Cette action :
    1. Valide le code CCAM proposé
    2. Enregistre la décision sur la blockchain
    3. Met à jour le statut de l'acte
    4. Crée une entrée d'audit
    """
    acte_service = ActeService(db)
    blockchain_service = BlockchainService()
    
    # Récupérer l'acte
    acte = acte_service.get_acte_by_id(acte_id)
    if not acte:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acte non trouvé"
        )
    
    # Vérifier les permissions
    if acte.createur_id != current_user.id and current_user.role.value not in ["admin", "medecin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    # Vérifier que l'acte n'est pas déjà validé
    if acte.statut in ["valide", "rejete"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Acte déjà validé"
        )
    
    # Vérifier le score de confiance si pas de force_validation
    if not validation_data.force_validation and acte.score_confiance and acte.score_confiance < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Score de confiance trop faible. Utilisez force_validation=true pour forcer."
        )
    
    try:
        # Valider l'acte
        updated_acte = acte_service.validate_acte(
            acte_id=acte_id,
            code_ccam_final=validation_data.code_ccam_final,
            validateur_id=current_user.id,
            justification=validation_data.justification
        )
        
        # Enregistrer sur la blockchain
        transaction_hash = await blockchain_service.record_validation(
            acte_id=acte_id,
            code_ccam=validation_data.code_ccam_final,
            version_ccam=acte.code_ccam_suggere,  # Version utilisée pour la suggestion
            auteur_id=current_user.id,
            justification=validation_data.justification or "Validation standard"
        )
        
        # Mettre à jour l'acte avec le hash de transaction
        acte_service.update_acte_blockchain_info(
            acte_id=acte_id,
            transaction_hash=transaction_hash
        )
        
        # Enregistrer l'action d'audit
        background_tasks.add_task(
            acte_service.log_audit_action,
            acte_id=acte_id,
            user_id=current_user.id,
            action="validate_acte",
            entity_type="acte",
            new_values={
                "code_ccam_final": validation_data.code_ccam_final,
                "statut": "valide",
                "transaction_hash": transaction_hash
            }
        )
        
        return {
            "message": "Acte validé avec succès",
            "acte_id": acte_id,
            "transaction_hash": transaction_hash,
            "statut": "valide"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la validation: {str(e)}"
        )

@router.post("/{acte_id}/override", response_model=OverrideResponse)
async def create_override(
    acte_id: int,
    override_data: OverrideCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Créer un override (correction manuelle) pour un acte.
    
    Permet de corriger un code CCAM suggéré par l'IA avec justification obligatoire.
    L'override est enregistré sur la blockchain pour traçabilité.
    """
    acte_service = ActeService(db)
    override_service = OverrideService(db)
    blockchain_service = BlockchainService()
    
    # Récupérer l'acte
    acte = acte_service.get_acte_by_id(acte_id)
    if not acte:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acte non trouvé"
        )
    
    # Vérifier les permissions
    if acte.createur_id != current_user.id and current_user.role.value not in ["admin", "medecin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    # Vérifier que l'acte n'est pas déjà validé
    if acte.statut in ["valide", "rejete"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de créer un override sur un acte déjà validé"
        )
    
    try:
        # Créer l'override
        override = override_service.create_override(
            acte_id=acte_id,
            utilisateur_id=current_user.id,
            code_ccam_original=override_data.code_ccam_original,
            code_ccam_override=override_data.code_ccam_override,
            justification=override_data.justification,
            type_override=override_data.type_override
        )
        
        # Enregistrer l'override sur la blockchain
        transaction_hash = await blockchain_service.record_override(
            override_id=override.id,
            acte_id=acte_id,
            code_ccam_original=override_data.code_ccam_original,
            code_ccam_override=override_data.code_ccam_override,
            auteur_id=current_user.id,
            justification=override_data.justification
        )
        
        # Mettre à jour l'override avec le hash de transaction
        override_service.update_override_blockchain_info(
            override_id=override.id,
            transaction_hash=transaction_hash
        )
        
        # Mettre à jour l'acte avec le nouveau code
        acte_service.update_acte_suggestion(
            acte_id=acte_id,
            code_suggere=override_data.code_ccam_override
        )
        
        # Enregistrer l'action d'audit
        background_tasks.add_task(
            acte_service.log_audit_action,
            acte_id=acte_id,
            user_id=current_user.id,
            action="create_override",
            entity_type="override",
            new_values={
                "override_id": override.id,
                "code_ccam_override": override_data.code_ccam_override,
                "transaction_hash": transaction_hash
            }
        )
        
        return override
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de l'override: {str(e)}"
        )

@router.get("/{acte_id}/overrides", response_model=List[OverrideResponse])
async def get_acte_overrides(
    acte_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Récupérer tous les overrides d'un acte.
    """
    acte_service = ActeService(db)
    override_service = OverrideService(db)
    
    # Récupérer l'acte
    acte = acte_service.get_acte_by_id(acte_id)
    if not acte:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acte non trouvé"
        )
    
    # Vérifier les permissions
    if acte.createur_id != current_user.id and current_user.role.value not in ["admin", "audit"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    overrides = override_service.get_overrides_by_acte(acte_id)
    return overrides

@router.post("/{acte_id}/reject")
async def reject_acte(
    acte_id: int,
    reason: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Rejeter un acte (marquer comme invalide).
    
    Utilisé quand un acte ne peut pas être codé correctement ou présente
    des problèmes de conformité.
    """
    acte_service = ActeService(db)
    blockchain_service = BlockchainService()
    
    # Récupérer l'acte
    acte = acte_service.get_acte_by_id(acte_id)
    if not acte:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acte non trouvé"
        )
    
    # Vérifier les permissions
    if acte.createur_id != current_user.id and current_user.role.value not in ["admin", "medecin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    # Vérifier que l'acte n'est pas déjà validé
    if acte.statut in ["valide", "rejete"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Acte déjà traité"
        )
    
    try:
        # Rejeter l'acte
        updated_acte = acte_service.reject_acte(
            acte_id=acte_id,
            validateur_id=current_user.id,
            reason=reason
        )
        
        # Enregistrer le rejet sur la blockchain
        transaction_hash = await blockchain_service.record_rejection(
            acte_id=acte_id,
            auteur_id=current_user.id,
            reason=reason
        )
        
        # Mettre à jour l'acte avec le hash de transaction
        acte_service.update_acte_blockchain_info(
            acte_id=acte_id,
            transaction_hash=transaction_hash
        )
        
        # Enregistrer l'action d'audit
        background_tasks.add_task(
            acte_service.log_audit_action,
            acte_id=acte_id,
            user_id=current_user.id,
            action="reject_acte",
            entity_type="acte",
            new_values={
                "statut": "rejete",
                "reason": reason,
                "transaction_hash": transaction_hash
            }
        )
        
        return {
            "message": "Acte rejeté avec succès",
            "acte_id": acte_id,
            "transaction_hash": transaction_hash,
            "statut": "rejete"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du rejet: {str(e)}"
        )