"""
Service IA principal pour la génération de suggestions CCAM
Gère l'interaction avec les LLM et le traitement des suggestions
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

import openai
from pydantic import BaseModel, Field
import redis

from ..prompts.ccam_prompts import CCAMPrompts
from ..models.acte_model import ActeModel
from ..utils.cache_manager import CacheManager
from ..utils.rule_engine import RuleEngine

logger = logging.getLogger(__name__)

class Suggestion(BaseModel):
    """Modèle pour une suggestion de code CCAM"""
    code: str = Field(..., description="Code CCAM proposé")
    libelle: str = Field(..., description="Libellé du code")
    modificateurs: List[str] = Field(default=[], description="Modificateurs compatibles")
    score_confiance: float = Field(..., ge=0, le=100, description="Score de confiance (0-100)")
    explication: str = Field(..., description="Explication du choix")
    incompatibilites: List[str] = Field(default=[], description="Incompatibilités détectées")

class AISuggestionResponse(BaseModel):
    """Réponse complète de l'IA pour les suggestions"""
    suggestions: List[Suggestion] = Field(..., description="Liste des suggestions")
    score_confiance_global: float = Field(..., ge=0, le=100, description="Score global de confiance")
    explication_globale: str = Field(..., description="Explication globale")
    questions_clarification: List[str] = Field(default=[], description="Questions de clarification")
    alertes: List[str] = Field(default=[], description="Alertes importantes")

class AIService:
    """Service principal pour l'IA de codage CCAM"""
    
    def __init__(self, 
                 openai_api_key: str,
                 redis_url: str = "redis://localhost:6379/0",
                 model: str = "gpt-4",
                 max_tokens: int = 2000,
                 temperature: float = 0.1):
        """
        Initialiser le service IA
        
        Args:
            openai_api_key: Clé API OpenAI
            redis_url: URL Redis pour le cache
            model: Modèle LLM à utiliser
            max_tokens: Nombre maximum de tokens
            temperature: Température pour la génération
        """
        self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Initialiser les composants
        self.cache_manager = CacheManager(redis_url)
        self.rule_engine = RuleEngine()
        self.acte_model = ActeModel()
        
        logger.info(f"Service IA initialisé avec le modèle {model}")

    async def generate_suggestions(self, 
                                 acte_data: Dict[str, Any], 
                                 force_regenerate: bool = False) -> AISuggestionResponse:
        """
        Générer des suggestions de codes CCAM pour un acte
        
        Args:
            acte_data: Données de l'acte
            force_regenerate: Forcer la régénération même si en cache
            
        Returns:
            AISuggestionResponse: Suggestions générées
        """
        try:
            # Créer une clé de cache basée sur les données de l'acte
            cache_key = self._create_cache_key(acte_data)
            
            # Vérifier le cache si pas de force_regenerate
            if not force_regenerate:
                cached_result = await self.cache_manager.get(cache_key)
                if cached_result:
                    logger.info(f"Résultat trouvé en cache pour l'acte {acte_data.get('numero_acte')}")
                    return AISuggestionResponse(**cached_result)
            
            # Extraire les informations cliniques
            extracted_info = await self._extract_clinical_info(acte_data)
            
            # Formater le prompt principal
            prompt = CCAMPrompts.format_prompt(
                "main_suggestion",
                type_acte=acte_data.get("type_acte", ""),
                description_clinique=acte_data.get("description_clinique", ""),
                materiel_utilise=acte_data.get("materiel_utilise", ""),
                duree_acte=str(acte_data.get("duree_acte", "")),
                modificateurs=", ".join(acte_data.get("modificateurs", [])),
                etablissement=acte_data.get("etablissement", ""),
                service=acte_data.get("service", "")
            )
            
            # Appeler le LLM
            llm_response = await self._call_llm(prompt)
            
            # Parser la réponse JSON
            parsed_response = self._parse_llm_response(llm_response)
            
            # Valider et enrichir les suggestions avec les règles métier
            enriched_suggestions = await self._enrich_suggestions(parsed_response, extracted_info)
            
            # Créer la réponse finale
            ai_response = AISuggestionResponse(
                suggestions=enriched_suggestions["suggestions"],
                score_confiance_global=enriched_suggestions["score_confiance_global"],
                explication_globale=enriched_suggestions["explication_globale"],
                questions_clarification=enriched_suggestions.get("questions_clarification", []),
                alertes=enriched_suggestions.get("alertes", [])
            )
            
            # Mettre en cache le résultat
            await self.cache_manager.set(cache_key, ai_response.dict(), ttl=3600)
            
            # Enregistrer les métriques
            await self._record_metrics(acte_data, ai_response)
            
            logger.info(f"Suggestions générées pour l'acte {acte_data.get('numero_acte')} avec score {ai_response.score_confiance_global}")
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de suggestions: {str(e)}")
            raise

    async def validate_suggestion(self, 
                                code_ccam: str, 
                                acte_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valider une suggestion de code CCAM
        
        Args:
            code_ccam: Code CCAM à valider
            acte_context: Contexte de l'acte
            
        Returns:
            Dict: Résultat de la validation
        """
        try:
            # Formater le prompt de validation
            prompt = CCAMPrompts.format_prompt(
                "validation",
                code_propose=code_ccam,
                contexte_acte=json.dumps(acte_context, ensure_ascii=False)
            )
            
            # Appeler le LLM
            llm_response = await self._call_llm(prompt)
            
            # Parser la réponse
            validation_result = self._parse_llm_response(llm_response)
            
            # Ajouter la validation par les règles métier
            rule_validation = await self.rule_engine.validate_code(code_ccam, acte_context)
            
            # Combiner les résultats
            final_validation = {
                **validation_result,
                "rule_validation": rule_validation,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return final_validation
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation: {str(e)}")
            raise

    async def learn_from_override(self, 
                                override_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apprendre à partir d'un override (correction humaine)
        
        Args:
            override_data: Données de l'override
            
        Returns:
            Dict: Analyse de l'apprentissage
        """
        try:
            # Formater le prompt d'apprentissage
            prompt = CCAMPrompts.format_prompt(
                "learning",
                code_suggere=override_data["code_ccam_original"],
                code_final=override_data["code_ccam_override"],
                justification=override_data["justification"],
                contexte=json.dumps(override_data["contexte"], ensure_ascii=False)
            )
            
            # Appeler le LLM
            llm_response = await self._call_llm(prompt)
            
            # Parser la réponse
            learning_analysis = self._parse_llm_response(llm_response)
            
            # Enregistrer l'apprentissage
            await self._record_learning(override_data, learning_analysis)
            
            return learning_analysis
            
        except Exception as e:
            logger.error(f"Erreur lors de l'apprentissage: {str(e)}")
            raise

    async def detect_anomalies(self, acte_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Détecter les anomalies dans un acte
        
        Args:
            acte_data: Données de l'acte
            
        Returns:
            Dict: Anomalies détectées
        """
        try:
            # Formater le prompt de détection d'anomalies
            prompt = CCAMPrompts.format_prompt(
                "anomaly_detection",
                acte_details=json.dumps(acte_data, ensure_ascii=False)
            )
            
            # Appeler le LLM
            llm_response = await self._call_llm(prompt)
            
            # Parser la réponse
            anomalies = self._parse_llm_response(llm_response)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection d'anomalies: {str(e)}")
            raise

    async def _call_llm(self, prompt: str) -> str:
        """Appeler le LLM avec un prompt donné"""
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Tu es un expert en codage CCAM français."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erreur lors de l'appel au LLM: {str(e)}")
            raise

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parser la réponse JSON du LLM"""
        try:
            # Extraire le JSON de la réponse
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("Aucun JSON trouvé dans la réponse")
            
            json_str = response[json_start:json_end]
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de parsing JSON: {str(e)}")
            logger.error(f"Réponse LLM: {response}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors du parsing de la réponse: {str(e)}")
            raise

    async def _extract_clinical_info(self, acte_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraire les informations cliniques pertinentes"""
        try:
            # Formater le prompt d'extraction
            prompt = CCAMPrompts.format_prompt(
                "extraction",
                texte_clinique=acte_data.get("description_clinique", "")
            )
            
            # Appeler le LLM
            llm_response = await self._call_llm(prompt)
            
            # Parser la réponse
            extracted_info = self._parse_llm_response(llm_response)
            
            return extracted_info
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction d'informations: {str(e)}")
            return {}

    async def _enrich_suggestions(self, 
                                parsed_response: Dict[str, Any], 
                                extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """Enrichir les suggestions avec les règles métier"""
        try:
            enriched_suggestions = []
            
            for suggestion in parsed_response.get("suggestions", []):
                # Valider le code avec les règles métier
                rule_validation = await self.rule_engine.validate_code(
                    suggestion["code"], 
                    extracted_info
                )
                
                # Enrichir la suggestion
                enriched_suggestion = {
                    **suggestion,
                    "rule_validation": rule_validation,
                    "extracted_info": extracted_info
                }
                
                # Ajuster le score de confiance selon les règles
                if rule_validation.get("is_valid", True):
                    enriched_suggestion["score_confiance"] = min(
                        enriched_suggestion["score_confiance"] + 5, 
                        100
                    )
                else:
                    enriched_suggestion["score_confiance"] = max(
                        enriched_suggestion["score_confiance"] - 10, 
                        0
                    )
                
                enriched_suggestions.append(enriched_suggestion)
            
            return {
                "suggestions": enriched_suggestions,
                "score_confiance_global": parsed_response.get("score_confiance_global", 0),
                "explication_globale": parsed_response.get("explication_globale", ""),
                "questions_clarification": parsed_response.get("questions_clarification", []),
                "alertes": parsed_response.get("alertes", [])
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enrichissement des suggestions: {str(e)}")
            return parsed_response

    def _create_cache_key(self, acte_data: Dict[str, Any]) -> str:
        """Créer une clé de cache pour l'acte"""
        key_parts = [
            acte_data.get("type_acte", ""),
            acte_data.get("description_clinique", "")[:100],  # Limiter la longueur
            str(acte_data.get("duree_acte", "")),
            ",".join(sorted(acte_data.get("modificateurs", [])))
        ]
        return f"ccam_suggestion:{hash(''.join(key_parts))}"

    async def _record_metrics(self, acte_data: Dict[str, Any], response: AISuggestionResponse):
        """Enregistrer les métriques de performance"""
        try:
            metrics = {
                "acte_id": acte_data.get("id"),
                "numero_acte": acte_data.get("numero_acte"),
                "score_confiance": response.score_confiance_global,
                "nombre_suggestions": len(response.suggestions),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Enregistrer dans Redis pour les métriques
            await self.cache_manager.set(
                f"metrics:{acte_data.get('numero_acte')}", 
                metrics, 
                ttl=86400  # 24h
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement des métriques: {str(e)}")

    async def _record_learning(self, override_data: Dict[str, Any], learning_analysis: Dict[str, Any]):
        """Enregistrer les données d'apprentissage"""
        try:
            learning_data = {
                "override_data": override_data,
                "learning_analysis": learning_analysis,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Enregistrer dans Redis pour l'apprentissage
            await self.cache_manager.set(
                f"learning:{override_data.get('override_id')}", 
                learning_data, 
                ttl=604800  # 7 jours
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de l'apprentissage: {str(e)}")

    async def get_performance_metrics(self, date_debut: Optional[datetime] = None, 
                                    date_fin: Optional[datetime] = None) -> Dict[str, Any]:
        """Récupérer les métriques de performance"""
        try:
            # TODO: Implémenter la récupération des métriques depuis Redis/DB
            return {
                "total_suggestions": 0,
                "score_moyen": 0.0,
                "taux_validation": 0.0,
                "taux_override": 0.0
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques: {str(e)}")
            return {}