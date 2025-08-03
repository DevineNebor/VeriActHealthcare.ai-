"""
Prompts pour l'agent IA de codage CCAM
Contient les templates de prompts pour différentes tâches de codage médical
"""

from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class CCAMPrompt:
    """Classe pour représenter un prompt CCAM"""
    name: str
    template: str
    variables: List[str]
    description: str

class CCAMPrompts:
    """Collection de prompts pour l'agent IA CCAM"""
    
    # Prompt principal pour la suggestion de codes CCAM
    MAIN_SUGGESTION_PROMPT = CCAMPrompt(
        name="main_suggestion",
        template="""Tu es un copilote expert de codage CCAM en radiologie interventionnelle et médecine interventionnelle.

CONTEXTE:
- Tu dois proposer des codes CCAM (Classification Commune des Actes Médicaux) français
- Les codes CCAM sont au format: 4 lettres + 3 chiffres (ex: HHFA001)
- Tu dois tenir compte des modificateurs compatibles
- Tu dois vérifier les incompatibilités entre codes et modificateurs

ACTE À CODER:
Type d'acte: {type_acte}
Description clinique: {description_clinique}
Matériel utilisé: {materiel_utilise}
Durée: {duree_acte} minutes
Modificateurs existants: {modificateurs}
Établissement: {etablissement}
Service: {service}

TÂCHE:
Propose jusqu'à 3 codes CCAM avec modificateurs compatibles pour cet acte.

FORMAT DE RÉPONSE:
```json
{{
  "suggestions": [
    {{
      "code": "HHFA001",
      "libelle": "Angioplastie coronaire par ballonnet",
      "modificateurs": ["1", "2"],
      "score_confiance": 95,
      "explication": "Acte d'angioplastie coronaire standard avec pose de stent",
      "incompatibilites": ["Modificateur 3 incompatible avec ce code"]
    }}
  ],
  "score_confiance_global": 85,
  "explication_globale": "Acte d'angioplastie coronaire bien documenté avec matériel standard",
  "questions_clarification": [
    "Précision sur le type de stent utilisé (métallique, actif, bioabsorbable)?"
  ],
  "alertes": [
    "Vérifier la compatibilité avec les antécédents du patient"
  ]
}}
```

RÈGLES IMPORTANTES:
1. Propose uniquement des codes CCAM valides et actifs
2. Vérifie la compatibilité des modificateurs
3. Donne un score de confiance réaliste (0-100)
4. Si incertain, pose des questions de clarification
5. Signale les incompatibilités ou alertes
6. Explique brièvement le choix de chaque code""",
        variables=[
            "type_acte", "description_clinique", "materiel_utilise", 
            "duree_acte", "modificateurs", "etablissement", "service"
        ],
        description="Prompt principal pour la suggestion de codes CCAM"
    )

    # Prompt pour la validation et correction
    VALIDATION_PROMPT = CCAMPrompt(
        name="validation",
        template="""Tu es un expert en validation de codage CCAM.

CODE PROPOSÉ:
{code_propose}

CONTEXTE DE L'ACTE:
{contexte_acte}

TÂCHE:
Valide ce code CCAM et propose des corrections si nécessaire.

FORMAT DE RÉPONSE:
```json
{{
  "validation": {{
    "is_valid": true,
    "score_validation": 90,
    "commentaires": "Code approprié pour cet acte",
    "corrections_suggerees": []
  }},
  "verification_regles": [
    "✓ Code actif dans la nomenclature",
    "✓ Modificateurs compatibles",
    "✓ Cohérence avec le contexte clinique"
  ],
  "alertes": []
}}
```""",
        variables=["code_propose", "contexte_acte"],
        description="Prompt pour la validation de codes CCAM"
    )

    # Prompt pour l'extraction d'informations cliniques
    EXTRACTION_PROMPT = CCAMPrompt(
        name="extraction",
        template="""Tu es un expert en extraction d'informations médicales.

TEXTE CLINIQUE:
{texte_clinique}

TÂCHE:
Extrais les informations pertinentes pour le codage CCAM.

FORMAT DE RÉPONSE:
```json
{{
  "type_acte": "Angioplastie coronaire",
  "localisation": "Artère coronaire droite",
  "technique": "Pose de stent",
  "materiel": ["Guide", "Ballonnet", "Stent métallique"],
  "duree_estimee": 45,
  "modificateurs_implicites": ["1", "2"],
  "complexite": "standard",
  "complications": [],
  "contre_indications": []
}}
```""",
        variables=["texte_clinique"],
        description="Prompt pour l'extraction d'informations cliniques"
    )

    # Prompt pour l'apprentissage à partir des overrides
    LEARNING_PROMPT = CCAMPrompt(
        name="learning",
        template="""Tu es un agent IA qui apprend à partir des corrections humaines.

SITUATION:
Code suggéré par l'IA: {code_suggere}
Code final choisi: {code_final}
Justification de la correction: {justification}
Contexte de l'acte: {contexte}

TÂCHE:
Analyse cette correction pour améliorer les futures suggestions.

FORMAT DE RÉPONSE:
```json
{{
  "analyse": {{
    "type_erreur": "incomprehension_contexte",
    "facteurs_cles": ["Terminologie spécifique", "Contexte clinique complexe"],
    "lecons_apprises": ["Reconnaître les termes techniques spécifiques"]
  }},
  "améliorations_suggerees": [
    "Ajouter des synonymes pour les termes techniques",
    "Améliorer la compréhension du contexte clinique"
  ],
  "patterns_identifies": [
    "Confusion entre techniques similaires"
  ]
}}
```""",
        variables=["code_suggere", "code_final", "justification", "contexte"],
        description="Prompt pour l'apprentissage à partir des corrections"
    )

    # Prompt pour la détection d'anomalies
    ANOMALY_DETECTION_PROMPT = CCAMPrompt(
        name="anomaly_detection",
        template="""Tu es un expert en détection d'anomalies dans le codage CCAM.

ACTE À ANALYSER:
{acte_details}

TÂCHE:
Détecte les anomalies potentielles dans ce codage.

FORMAT DE RÉPONSE:
```json
{{
  "anomalies_detectees": [
    {{
      "type": "incompatibilite_modificateur",
      "severite": "elevee",
      "description": "Modificateur 3 incompatible avec ce code",
      "suggestion": "Utiliser le modificateur 1 ou 2"
    }}
  ],
  "score_anomalie": 75,
  "recommandations": [
    "Vérifier la compatibilité des modificateurs",
    "Contrôler la cohérence avec le contexte clinique"
  ]
}}
```""",
        variables=["acte_details"],
        description="Prompt pour la détection d'anomalies"
    )

    @classmethod
    def get_prompt(cls, prompt_name: str) -> CCAMPrompt:
        """Récupérer un prompt par son nom"""
        prompts = {
            "main_suggestion": cls.MAIN_SUGGESTION_PROMPT,
            "validation": cls.VALIDATION_PROMPT,
            "extraction": cls.EXTRACTION_PROMPT,
            "learning": cls.LEARNING_PROMPT,
            "anomaly_detection": cls.ANOMALY_DETECTION_PROMPT
        }
        return prompts.get(prompt_name)

    @classmethod
    def format_prompt(cls, prompt_name: str, **kwargs) -> str:
        """Formater un prompt avec les variables données"""
        prompt = cls.get_prompt(prompt_name)
        if not prompt:
            raise ValueError(f"Prompt '{prompt_name}' non trouvé")
        
        # Vérifier que toutes les variables requises sont présentes
        missing_vars = [var for var in prompt.variables if var not in kwargs]
        if missing_vars:
            raise ValueError(f"Variables manquantes pour le prompt '{prompt_name}': {missing_vars}")
        
        return prompt.template.format(**kwargs)

    @classmethod
    def list_prompts(cls) -> List[str]:
        """Lister tous les prompts disponibles"""
        return [
            "main_suggestion",
            "validation", 
            "extraction",
            "learning",
            "anomaly_detection"
        ]

# Exemples d'utilisation
if __name__ == "__main__":
    # Exemple de formatage du prompt principal
    try:
        formatted_prompt = CCAMPrompts.format_prompt(
            "main_suggestion",
            type_acte="Angioplastie coronaire",
            description_clinique="Pose de stent dans l'artère coronaire droite",
            materiel_utilise="Guide, ballonnet, stent métallique",
            duree_acte="45",
            modificateurs="1, 2",
            etablissement="CHU de Paris",
            service="Cardiologie interventionnelle"
        )
        print("Prompt formaté avec succès!")
        print(formatted_prompt[:200] + "...")
    except Exception as e:
        print(f"Erreur: {e}")