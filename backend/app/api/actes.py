from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..core.database import get_db
from ..core.auth import get_current_user
from ..models import Acte, Utilisateur
from ..schemas.acte import ActeCreate, ActeResponse, ActeList, ActeUpdate
from ..services.acte_service import ActeService
from ..services.blockchain_service import BlockchainService

router = APIRouter()

@router.post("/", response_model=ActeResponse, status_code=status.HTTP_201_CREATED)
async def create_acte(
    acte_data: ActeCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Créer un nouvel acte médical.
    
    - **numero_acte**: Numéro unique de l'acte
    - **patient_id**: ID pseudonymisé du patient
    - **type_acte**: Type d'acte médical
    - **description_clinique**: Description clinique détaillée
    - **materiel_utilise**: Matériel utilisé (optionnel)
    - **duree_acte**: Durée en minutes (optionnel)
    - **modificateurs**: Liste des modificateurs CCAM (optionnel)
    - **etablissement**: Établissement de santé
    - **service**: Service médical (optionnel)
    - **date_acte**: Date de réalisation de l'acte
    """
    acte_service = ActeService(db)
    
    # Vérifier si le numéro d'acte existe déjà
    existing_acte = acte_service.get_acte_by_numero(acte_data.numero_acte)
    if existing_acte:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un acte avec ce numéro existe déjà"
        )
    
    # Créer l'acte
    acte = acte_service.create_acte(acte_data, current_user.id)
    
    # Déclencher la suggestion IA en arrière-plan
    # TODO: Ajouter une tâche Celery pour la suggestion IA
    
    return acte

@router.get("/", response_model=ActeList)
async def get_actes(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    statut: Optional[str] = Query(None, description="Filtrer par statut"),
    etablissement: Optional[str] = Query(None, description="Filtrer par établissement"),
    date_debut: Optional[datetime] = Query(None, description="Date de début"),
    date_fin: Optional[datetime] = Query(None, description="Date de fin"),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Récupérer la liste des actes avec pagination et filtres.
    """
    acte_service = ActeService(db)
    actes, total = acte_service.get_actes(
        skip=skip,
        limit=limit,
        statut=statut,
        etablissement=etablissement,
        date_debut=date_debut,
        date_fin=date_fin,
        user_id=current_user.id
    )
    
    pages = (total + limit - 1) // limit
    page = (skip // limit) + 1
    
    return ActeList(
        actes=actes,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )

@router.get("/{acte_id}", response_model=ActeResponse)
async def get_acte(
    acte_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Récupérer un acte par son ID.
    """
    acte_service = ActeService(db)
    acte = acte_service.get_acte_by_id(acte_id)
    
    if not acte:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acte non trouvé"
        )
    
    # Vérifier les permissions (seul le créateur ou un admin peut voir l'acte)
    if acte.createur_id != current_user.id and current_user.role.value not in ["admin", "audit"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    return acte

@router.put("/{acte_id}", response_model=ActeResponse)
async def update_acte(
    acte_id: int,
    acte_data: ActeUpdate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Mettre à jour un acte existant.
    """
    acte_service = ActeService(db)
    acte = acte_service.get_acte_by_id(acte_id)
    
    if not acte:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acte non trouvé"
        )
    
    # Vérifier les permissions
    if acte.createur_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    # Vérifier que l'acte n'est pas déjà validé
    if acte.statut in ["valide", "rejete"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de modifier un acte déjà validé"
        )
    
    updated_acte = acte_service.update_acte(acte_id, acte_data)
    return updated_acte

@router.delete("/{acte_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_acte(
    acte_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Supprimer un acte (soft delete).
    """
    acte_service = ActeService(db)
    acte = acte_service.get_acte_by_id(acte_id)
    
    if not acte:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acte non trouvé"
        )
    
    # Vérifier les permissions
    if acte.createur_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    # Vérifier que l'acte n'est pas déjà validé
    if acte.statut in ["valide", "rejete"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer un acte déjà validé"
        )
    
    acte_service.delete_acte(acte_id)
    return None