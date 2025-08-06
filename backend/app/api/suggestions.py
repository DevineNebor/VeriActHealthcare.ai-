from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..core.auth import get_current_user
from ..models import Utilisateur
from ..schemas.acte import ActeSuggestion
from ..services.ai_service import AIService
from ..services.acte_service import ActeService

router = APIRouter()

@router.get("/{acte_id}", response_model=ActeSuggestion)
async def get_suggestions(
    acte_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Récupérer les suggestions de codes CCAM pour un acte.
    
    Retourne jusqu'à 3 suggestions de codes CCAM avec :
    - Score de confiance
    - Explication
    - Questions de clarification si nécessaire
    """
    acte_service = ActeService(db)
    ai_service = AIService()
    
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
    
    # Générer les suggestions IA
    try:
        suggestions = await ai_service.generate_suggestions(acte)
        
        # Mettre à jour l'acte avec la meilleure suggestion
        if suggestions.suggestions:
            best_suggestion = suggestions.suggestions[0]
            acte_service.update_acte_suggestion(
                acte_id=acte_id,
                code_suggere=best_suggestion.get("code"),
                score_confiance=suggestions.score_confiance
            )
        
        return suggestions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération des suggestions: {str(e)}"
        )

@router.post("/{acte_id}/regenerate", response_model=ActeSuggestion)
async def regenerate_suggestions(
    acte_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Régénérer les suggestions de codes CCAM pour un acte.
    
    Force la régénération des suggestions, utile si les premières suggestions
    ne sont pas satisfaisantes.
    """
    acte_service = ActeService(db)
    ai_service = AIService()
    
    # Récupérer l'acte
    acte = acte_service.get_acte_by_id(acte_id)
    if not acte:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acte non trouvé"
        )
    
    # Vérifier les permissions
    if acte.createur_id != current_user.id and current_user.role.value not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    # Régénérer les suggestions
    try:
        suggestions = await ai_service.generate_suggestions(acte, force_regenerate=True)
        
        # Mettre à jour l'acte avec la nouvelle suggestion
        if suggestions.suggestions:
            best_suggestion = suggestions.suggestions[0]
            acte_service.update_acte_suggestion(
                acte_id=acte_id,
                code_suggere=best_suggestion.get("code"),
                score_confiance=suggestions.score_confiance
            )
        
        # Enregistrer l'action d'audit
        background_tasks.add_task(
            acte_service.log_audit_action,
            acte_id=acte_id,
            user_id=current_user.id,
            action="regenerate_suggestions",
            entity_type="acte"
        )
        
        return suggestions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la régénération des suggestions: {str(e)}"
        )

@router.post("/{acte_id}/feedback")
async def submit_feedback(
    acte_id: int,
    feedback_data: dict,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Soumettre un feedback sur les suggestions IA.
    
    Permet d'améliorer le modèle IA en fournissant des retours sur la qualité
    des suggestions générées.
    """
    acte_service = ActeService(db)
    ai_service = AIService()
    
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
    
    try:
        # Enregistrer le feedback pour l'apprentissage
        await ai_service.record_feedback(
            acte_id=acte_id,
            user_id=current_user.id,
            feedback=feedback_data
        )
        
        # Enregistrer l'action d'audit
        acte_service.log_audit_action(
            acte_id=acte_id,
            user_id=current_user.id,
            action="submit_feedback",
            entity_type="acte",
            metadata={"feedback": feedback_data}
        )
        
        return {"message": "Feedback enregistré avec succès"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'enregistrement du feedback: {str(e)}"
        )

@router.get("/batch/status")
async def get_batch_suggestions_status(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Récupérer le statut des suggestions en lot.
    
    Permet de suivre l'avancement des suggestions générées en arrière-plan
    pour un ensemble d'actes.
    """
    if current_user.role.value not in ["admin", "audit"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    # TODO: Implémenter le suivi des tâches en lot
    return {
        "pending_tasks": 0,
        "completed_tasks": 0,
        "failed_tasks": 0,
        "estimated_completion": None
    }