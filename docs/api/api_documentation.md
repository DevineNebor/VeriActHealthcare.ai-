# Documentation API - CCAM AI + Blockchain

## Vue d'ensemble

L'API CCAM AI + Blockchain fournit une interface REST complète pour la gestion des actes médicaux, la génération de suggestions IA, la validation et l'audit trail. L'API est construite avec FastAPI et utilise OpenAPI/Swagger pour la documentation interactive.

## Base URL

- **Développement** : `http://localhost:8000`
- **Production** : `https://api.ccam-ai.com`

## Authentification

L'API utilise OAuth2 avec JWT pour l'authentification. Tous les endpoints (sauf `/auth`) nécessitent un token d'accès valide.

### Obtenir un token

```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=password
```

### Utiliser le token

```http
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Authentification

#### POST /auth/token
Obtenir un token d'accès.

**Paramètres :**
- `username` (string, requis) : Email de l'utilisateur
- `password` (string, requis) : Mot de passe

**Réponse :**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### POST /auth/refresh
Rafraîchir un token expiré.

**Paramètres :**
- `refresh_token` (string, requis) : Token de rafraîchissement

### 2. Gestion des actes

#### POST /actes
Créer un nouvel acte médical.

**Corps de la requête :**
```json
{
  "numero_acte": "ACTE-2024-001",
  "patient_id": "PAT-12345",
  "type_acte": "Angioplastie coronaire",
  "description_clinique": "Pose de stent dans l'artère coronaire droite",
  "materiel_utilise": "Guide, ballonnet, stent métallique",
  "duree_acte": 45,
  "modificateurs": ["1", "2"],
  "etablissement": "CHU de Paris",
  "service": "Cardiologie interventionnelle",
  "date_acte": "2024-01-15T10:30:00Z"
}
```

**Réponse :**
```json
{
  "id": 1,
  "numero_acte": "ACTE-2024-001",
  "patient_id": "PAT-12345",
  "type_acte": "Angioplastie coronaire",
  "description_clinique": "Pose de stent dans l'artère coronaire droite",
  "materiel_utilise": "Guide, ballonnet, stent métallique",
  "duree_acte": 45,
  "modificateurs": ["1", "2"],
  "etablissement": "CHU de Paris",
  "service": "Cardiologie interventionnelle",
  "date_acte": "2024-01-15T10:30:00Z",
  "code_ccam_suggere": null,
  "code_ccam_final": null,
  "score_confiance": null,
  "statut": "en_attente",
  "date_validation": null,
  "mode_traitement": "normal",
  "createur_id": 1,
  "validateur_id": null,
  "transaction_hash": null,
  "block_number": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### GET /actes
Récupérer la liste des actes avec pagination et filtres.

**Paramètres de requête :**
- `skip` (integer, optionnel) : Nombre d'éléments à ignorer (défaut: 0)
- `limit` (integer, optionnel) : Nombre d'éléments à retourner (défaut: 100, max: 1000)
- `statut` (string, optionnel) : Filtrer par statut
- `etablissement` (string, optionnel) : Filtrer par établissement
- `date_debut` (datetime, optionnel) : Date de début
- `date_fin` (datetime, optionnel) : Date de fin

**Réponse :**
```json
{
  "actes": [...],
  "total": 150,
  "page": 1,
  "size": 100,
  "pages": 2
}
```

#### GET /actes/{acte_id}
Récupérer un acte par son ID.

**Paramètres de chemin :**
- `acte_id` (integer, requis) : ID de l'acte

#### PUT /actes/{acte_id}
Mettre à jour un acte existant.

**Paramètres de chemin :**
- `acte_id` (integer, requis) : ID de l'acte

**Corps de la requête :**
```json
{
  "type_acte": "Angioplastie coronaire modifiée",
  "description_clinique": "Description mise à jour",
  "duree_acte": 50
}
```

#### DELETE /actes/{acte_id}
Supprimer un acte (soft delete).

**Paramètres de chemin :**
- `acte_id` (integer, requis) : ID de l'acte

### 3. Suggestions IA

#### GET /suggestions/{acte_id}
Récupérer les suggestions de codes CCAM pour un acte.

**Paramètres de chemin :**
- `acte_id` (integer, requis) : ID de l'acte

**Réponse :**
```json
{
  "acte_id": 1,
  "suggestions": [
    {
      "code": "HHFA001",
      "libelle": "Angioplastie coronaire par ballonnet",
      "modificateurs": ["1", "2"],
      "score_confiance": 95,
      "explication": "Acte d'angioplastie coronaire standard avec pose de stent",
      "incompatibilites": []
    },
    {
      "code": "HHFA002",
      "libelle": "Angioplastie coronaire avec pose de stent",
      "modificateurs": ["1"],
      "score_confiance": 85,
      "explication": "Alternative avec stent spécifique",
      "incompatibilites": ["Modificateur 2 incompatible"]
    }
  ],
  "score_confiance": 90,
  "explication": "Acte d'angioplastie coronaire bien documenté",
  "questions_clarification": [
    "Précision sur le type de stent utilisé?"
  ]
}
```

#### POST /suggestions/{acte_id}/regenerate
Régénérer les suggestions IA pour un acte.

**Paramètres de chemin :**
- `acte_id` (integer, requis) : ID de l'acte

#### POST /suggestions/{acte_id}/feedback
Soumettre un feedback sur les suggestions IA.

**Paramètres de chemin :**
- `acte_id` (integer, requis) : ID de l'acte

**Corps de la requête :**
```json
{
  "suggestion_utilisee": "HHFA001",
  "qualite_suggestion": 4,
  "commentaires": "Suggestion très pertinente",
  "corrections_apportees": ["Modificateur ajouté"]
}
```

### 4. Validation et Overrides

#### POST /validation/{acte_id}
Valider un acte avec un code CCAM final.

**Paramètres de chemin :**
- `acte_id` (integer, requis) : ID de l'acte

**Corps de la requête :**
```json
{
  "code_ccam_final": "HHFA001",
  "justification": "Code validé après vérification",
  "force_validation": false
}
```

**Réponse :**
```json
{
  "message": "Acte validé avec succès",
  "acte_id": 1,
  "transaction_hash": "0x1234567890abcdef...",
  "statut": "valide"
}
```

#### POST /validation/{acte_id}/override
Créer un override (correction manuelle) pour un acte.

**Paramètres de chemin :**
- `acte_id` (integer, requis) : ID de l'acte

**Corps de la requête :**
```json
{
  "code_ccam_original": "HHFA001",
  "code_ccam_override": "HHFA002",
  "justification": "Le code original ne correspondait pas au contexte clinique",
  "type_override": "correction"
}
```

**Réponse :**
```json
{
  "id": 1,
  "acte_id": 1,
  "utilisateur_id": 1,
  "code_ccam_original": "HHFA001",
  "code_ccam_override": "HHFA002",
  "justification": "Le code original ne correspondait pas au contexte clinique",
  "type_override": "correction",
  "signature_numerique": "0xabcdef...",
  "is_approved": false,
  "approved_by": null,
  "transaction_hash": "0x1234567890abcdef...",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### GET /validation/{acte_id}/overrides
Récupérer tous les overrides d'un acte.

**Paramètres de chemin :**
- `acte_id` (integer, requis) : ID de l'acte

#### POST /validation/{acte_id}/reject
Rejeter un acte.

**Paramètres de chemin :**
- `acte_id` (integer, requis) : ID de l'acte

**Corps de la requête :**
```json
{
  "reason": "Acte non conforme aux règles CCAM"
}
```

### 5. Audit Trail

#### GET /audit/{acte_id}
Récupérer la trace d'audit complète d'un acte.

**Paramètres de chemin :**
- `acte_id` (integer, requis) : ID de l'acte

**Paramètres de requête :**
- `skip` (integer, optionnel) : Nombre d'éléments à ignorer
- `limit` (integer, optionnel) : Nombre d'éléments à retourner
- `action_type` (string, optionnel) : Filtrer par type d'action
- `date_debut` (datetime, optionnel) : Date de début
- `date_fin` (datetime, optionnel) : Date de fin

**Réponse :**
```json
{
  "entries": [
    {
      "id": 1,
      "acte_id": 1,
      "action": "create_acte",
      "entity_type": "acte",
      "entity_id": 1,
      "timestamp": "2024-01-15T10:30:00Z",
      "utilisateur": "user@example.com",
      "old_values": null,
      "new_values": "{\"numero_acte\": \"ACTE-2024-001\", ...}",
      "transaction_hash": "0x1234567890abcdef..."
    }
  ],
  "total": 1,
  "page": 1,
  "size": 100,
  "pages": 1
}
```

#### GET /audit/{acte_id}/blockchain
Récupérer la trace blockchain d'un acte.

**Paramètres de chemin :**
- `acte_id` (integer, requis) : ID de l'acte

**Réponse :**
```json
{
  "acte_id": 1,
  "transactions": [
    {
      "hash": "0x1234567890abcdef...",
      "block_number": 12345,
      "timestamp": "2024-01-15T10:30:00Z",
      "method": "registerActe",
      "parameters": {...}
    }
  ],
  "total_transactions": 1
}
```

#### GET /audit/{acte_id}/integrity
Vérifier l'intégrité d'un acte.

**Paramètres de chemin :**
- `acte_id` (integer, requis) : ID de l'acte

**Réponse :**
```json
{
  "acte_id": 1,
  "integrity_verified": true,
  "last_verification": "2024-01-15T10:30:00Z",
  "details": "Toutes les données sont cohérentes",
  "blockchain_consistency": true
}
```

#### GET /audit/overrides/summary
Récupérer un résumé des overrides.

**Paramètres de requête :**
- `date_debut` (datetime, optionnel) : Date de début
- `date_fin` (datetime, optionnel) : Date de fin
- `etablissement` (string, optionnel) : Filtrer par établissement

**Réponse :**
```json
{
  "total_overrides": 25,
  "overrides_par_type": {
    "correction": 15,
    "precision": 8,
    "modificateur": 2
  },
  "taux_override": 0.05,
  "codes_les_plus_overrides": [
    {"code": "HHFA001", "count": 5},
    {"code": "HHFA002", "count": 3}
  ]
}
```

#### GET /audit/performance/metrics
Récupérer les métriques de performance.

**Paramètres de requête :**
- `date_debut` (datetime, optionnel) : Date de début
- `date_fin` (datetime, optionnel) : Date de fin

**Réponse :**
```json
{
  "total_actes": 1000,
  "actes_valides": 950,
  "actes_rejetes": 50,
  "taux_erreur": 0.05,
  "score_confiance_moyen": 87.5,
  "temps_traitement_moyen": 2.3,
  "overrides_par_jour": 12.5
}
```

#### GET /audit/compliance/report
Générer un rapport de conformité.

**Paramètres de requête :**
- `date_debut` (datetime, optionnel) : Date de début
- `date_fin` (datetime, optionnel) : Date de fin
- `etablissement` (string, optionnel) : Filtrer par établissement

**Réponse :**
```json
{
  "periode": "2024-01-01 à 2024-01-31",
  "conformite_globale": 0.95,
  "actes_audites": 1000,
  "violations_detectees": 25,
  "overrides_justifies": 50,
  "traçabilite_complete": true,
  "preuves_blockchain": true,
  "recommandations": [
    "Améliorer la formation sur les modificateurs",
    "Réviser les règles de validation automatique"
  ]
}
```

### 6. Administration

#### GET /admin/users
Récupérer la liste des utilisateurs (admin seulement).

#### POST /admin/users
Créer un nouvel utilisateur (admin seulement).

**Corps de la requête :**
```json
{
  "email": "nouveau@example.com",
  "username": "nouveau_user",
  "password": "motdepasse123",
  "nom": "Dupont",
  "prenom": "Jean",
  "role": "medecin",
  "specialite": "Cardiologie",
  "etablissement": "CHU de Paris"
}
```

#### GET /admin/metrics
Récupérer les métriques système (admin seulement).

**Réponse :**
```json
{
  "system_metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.4,
    "active_connections": 25
  },
  "application_metrics": {
    "requests_per_minute": 150,
    "average_response_time": 1.2,
    "error_rate": 0.02
  },
  "ai_metrics": {
    "suggestions_generated": 1250,
    "average_confidence": 88.5,
    "learning_samples": 45
  }
}
```

#### POST /admin/ccam/sync
Synchroniser le référentiel CCAM (admin seulement).

#### GET /admin/ccam/versions
Récupérer les versions du référentiel CCAM.

## Codes d'erreur

### Codes HTTP

- `200` : Succès
- `201` : Créé avec succès
- `400` : Requête invalide
- `401` : Non authentifié
- `403` : Non autorisé
- `404` : Ressource non trouvée
- `422` : Erreur de validation
- `500` : Erreur serveur interne

### Codes d'erreur spécifiques

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Le code CCAM n'est pas valide",
  "details": {
    "field": "code_ccam",
    "value": "INVALID123",
    "constraint": "Format CCAM requis: 4 lettres + 3 chiffres"
  }
}
```

## Rate Limiting

L'API applique des limites de taux pour prévenir l'abus :

- **Endpoints publics** : 100 requêtes/minute
- **Endpoints authentifiés** : 1000 requêtes/minute
- **Endpoints IA** : 50 requêtes/minute

## Pagination

Tous les endpoints de liste supportent la pagination :

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "size": 100,
  "pages": 2,
  "has_next": true,
  "has_prev": false
}
```

## Filtrage et tri

Les endpoints de liste supportent le filtrage et le tri :

```
GET /actes?statut=valide&etablissement=CHU&sort=date_acte&order=desc
```

## Webhooks

L'API supporte les webhooks pour les événements importants :

- `acte.created` : Nouvel acte créé
- `acte.validated` : Acte validé
- `override.created` : Override créé
- `audit.alert` : Alerte d'audit

## Documentation interactive

La documentation interactive est disponible à :
- **Swagger UI** : `/docs`
- **ReDoc** : `/redoc`
- **OpenAPI JSON** : `/openapi.json`

## Exemples d'utilisation

### Client Python

```python
import requests

# Authentification
response = requests.post('http://localhost:8000/auth/token', data={
    'username': 'user@example.com',
    'password': 'password'
})
token = response.json()['access_token']

# Créer un acte
headers = {'Authorization': f'Bearer {token}'}
acte_data = {
    'numero_acte': 'ACTE-2024-001',
    'patient_id': 'PAT-12345',
    'type_acte': 'Angioplastie coronaire',
    'description_clinique': 'Pose de stent...',
    'etablissement': 'CHU de Paris'
}

response = requests.post('http://localhost:8000/actes', 
                        json=acte_data, headers=headers)
acte = response.json()

# Obtenir les suggestions IA
response = requests.get(f'http://localhost:8000/suggestions/{acte["id"]}', 
                       headers=headers)
suggestions = response.json()
```

### Client JavaScript

```javascript
// Authentification
const authResponse = await fetch('http://localhost:8000/auth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'username=user@example.com&password=password'
});
const { access_token } = await authResponse.json();

// Créer un acte
const acteResponse = await fetch('http://localhost:8000/actes', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${access_token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        numero_acte: 'ACTE-2024-001',
        patient_id: 'PAT-12345',
        type_acte: 'Angioplastie coronaire',
        description_clinique: 'Pose de stent...',
        etablissement: 'CHU de Paris'
    })
});
const acte = await acteResponse.json();
```

## Support

Pour toute question ou problème avec l'API :

- **Documentation** : `/docs`
- **Support technique** : support@ccam-ai.com
- **Issues** : GitHub Issues
- **Discord** : Serveur communautaire

---

*Cette documentation est mise à jour régulièrement. Dernière mise à jour : Janvier 2024*