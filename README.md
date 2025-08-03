# CCAM AI + Blockchain Codage & Facturation Automatisée

## 1. Cas d'usage

### Problème
La facturation médicale via la nomenclature CCAM est complexe, sujette à des erreurs humaines, nécessite des validations multiples, engendre des rejets et ralentit les flux de trésorerie. Les services sont souvent sous-dotés en personnel administratif et manquent de traçabilité fiable, tout en devant rester conformes aux évolutions réglementaires.

### Produit
Une plateforme SaaS hybride combinant :
- Un **agent IA** copilot pour suggérer et expliquer les codes CCAM à partir du contexte clinique.
- Une **couche de règles formelles** pour garantir validité (incompatibilités, modificateurs).
- Une **chaine immuable (blockchain)** pour enregistrer, versionner et auditer chaque codage et override.
- Des **interfaces utilisateurs** pour médecins, administratifs et responsables facturation, avec boucles de feedback humain-in-the-loop.

### Proposition de valeur
> Automatiser le codage CCAM, vérifier en temps réel, garantir la conformité et fournir une trace immuable, tout en diminuant drastiquement la charge administrative et les rejets de facturation.

### Clients cibles
- Établissements de santé publics/privés avec ressources administratives limitées  
- Cliniques privées souhaitant accélérer leur cycle de facturation  
- Services de radiologie interventionnelle cherchant fiabilité et auditabilité  
- Revenue cycle management teams et contrôleurs de conformité  

## 2. Vision produit & plus-value

- **Réduction des erreurs de codage** grâce à une coopération entre règles et IA.  
- **Validation en temps réel** avec feedback et overrides tracés.  
- **Traçabilité immuable** : audit facile, preuve pour audits externes.  
- **Accélération du cash-flow** : moins de rejets, facturation plus rapide.  
- **Apprentissage continu** : l'agent s'améliore via corrections humaines.  
- **Conformité renforcée** : versioning du référentiel CCAM et enregistrement des règles appliquées.

## 3. Architecture technique

### 3.1. Vue d'ensemble
Un pipeline event-driven avec :  
- Ingestion d'un acte → suggestion IA hybride → validation / override → enregistrement par smart contract → facturation / export.

### 3.2. Composants

#### Backend (FastAPI)
- Gestion des actes, des utilisateurs, des règles CCAM.  
- Orchestration des suggestions IA.  
- Interface avec la blockchain (web3.py) pour enregistrer et lire les codages.  
- APIs pour frontend, audit, administration, versioning.  

#### Agent IA
- NLP pour extraire contexte clinique.  
- Modèle de suggestion (LLM + règles + knowledge graph).  
- Scoring de confiance et politique d'escalade.  
- Boucle de feedback / apprentissage actif.  

#### Smart Contracts (Blockchain)
- Enregistrement immuable des décisions (code, version, auteur, justification).  
- Gestion d'overrides avec signature et justification.  
- Stockage des métadonnées d'audit.  

#### Frontend (React)
- Saisie d'actes.  
- Affichage des suggestions et scores.  
- Override avec justification.  
- Dashboard de conformité / performance / versions.  

#### Data & Référentiel
- Référentiel CCAM versionné synchronisé localement.  
- Historique des actes, rejets, corrections.  
- Logs d'audit chiffrés associés aux preuves on-chain.

#### Infrastructure
- PostgreSQL : stockage principal.  
- Redis : cache & score.  
- Queue (RabbitMQ/Kafka) : découplage et résilience.  
- Noeud blockchain local / permissioned.  
- Services IA (proxy vers LLM, cache de prompts/responses).  

### 3.3. Sécurité
- Authentification OAuth2, RBAC.  
- Chiffrement en transit et au repos.  
- Signature numérique des overrides.  
- Logging tamper-evident.  
- Pseudonymisation / minimisation des données patients pour RGPD.  

### 3.4. Scalabilité & fiabilité
- Cache des lookups CCAM.  
- Traitement batch pour gros volumes.  
- Retry patterns / circuit breakers pour appels externes.  
- Shadow mode pour validation non invasive.  
- Monitoring (metrics, traces, alerting).

## 4. Flux de développement (Product Life Cycle)

1. **Découverte & validation** : interviews, collecte de données historiques (actes + rejets).  
2. **Prototype (shadow mode)** : suggestions IA + enregistrement on-chain sans impacter la facturation.  
3. **MVP** : boucle de validation avec overrides, intégration CCAM, dashboard.  
4. **Production** : seuils de confiance activés, passage en pleine facturation.  
5. **Apprentissage & évolution** : ajustement des modèles, mise à jour des règles CCAM, extension à d'autres nomenclatures.  

## 5. Structure du projet

```
/
├── backend/           # FastAPI service
├── blockchain/        # Smart contracts + deployment scripts (Hardhat)
├── agent_ai/          # IA agent pipeline, prompts, retraining scripts
├── frontend/          # React UI
├── infra/             # Docker-compose, deployment manifests, CI scripts
├── docs/              # Architecture design, onboarding, data schema
├── tests/             # Unit, integration, contract, model tests
├── scripts/           # Sync CCAM, migrate, analytics
├── .env.example       # Variables d'environnement
└── README.md          # Ce README descriptif
```

## 6. Exemples de prompt pour l'agent IA

Tu es un copilote de codage médical. Donne-moi jusqu'à 3 propositions de codes CCAM pour l'acte suivant : [note clinique], incluant le matériel utilisé, la durée, les modificateurs implicites. Donne un score de confiance sur 100, mentionne les incompatibilités possibles, et si tu es incertain, pose une question de clarification concise. Explique en deux phrases pourquoi ce code est proposé.

## 7. Déploiement local

```bash
# Installation rapide
cp .env.example .env
docker-compose up --build
cd blockchain && npm ci && npx hardhat run scripts/deploy.js --network local
# Seed référentiel CCAM
./scripts/sync_ccam.sh
# Lancer backend et frontend
```

## 8. Tests

- `tests/backend/` : simulation d'actes valides/invalide.  
- `tests/blockchain/` : intégrité du ledger, overrides.  
- `tests/agent/` : précision des suggestions vs historique.  
- CI : lint, security scan, test coverage gate.

## 9. Contribution et extension

- Modulariser la logique métier pour remplacer CCAM par d'autres nomenclatures.  
- Ajouter plugins pour intégration télétransmission, assurances tierces.  
- Remplacer le LLM par un modèle fine-tuné interne au fil du temps.

## 10. Metrics observées (pour suivre la réussite)

- Taux d'erreur de codage corrigé.
- Nombre d'actes traités par jour.
- % d'actes validés sans override humain.
- Délai moyen de facturation.
- Nombre de rejets évités.
- Score de confiance vs correction humaine.