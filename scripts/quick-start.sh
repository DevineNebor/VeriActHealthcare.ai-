#!/bin/bash

# Script de démarrage rapide pour CCAM AI + Blockchain
# Lance l'application complète en mode développement

set -e

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/infra/docker/docker-compose.yml"
ENV_FILE="$PROJECT_ROOT/.env"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de logging
log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] INFO: $1${NC}"
}

# Fonction pour vérifier les prérequis
check_prerequisites() {
    log "Vérification des prérequis..."
    
    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        error "Docker n'est pas installé"
        exit 1
    fi
    
    # Vérifier Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose n'est pas installé"
        exit 1
    fi
    
    # Vérifier Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js n'est pas installé"
        exit 1
    fi
    
    # Vérifier Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 n'est pas installé"
        exit 1
    fi
    
    log "Tous les prérequis sont satisfaits"
}

# Fonction pour configurer l'environnement
setup_environment() {
    log "Configuration de l'environnement..."
    
    # Créer le fichier .env s'il n'existe pas
    if [ ! -f "$ENV_FILE" ]; then
        info "Création du fichier .env..."
        cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
        warn "Veuillez configurer les variables d'environnement dans .env"
        warn "Particulièrement LLM_API_KEY, SECRET_KEY, et JWT_SECRET_KEY"
    else
        info "Fichier .env déjà existant"
    fi
    
    # Créer les répertoires nécessaires
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/data"
    mkdir -p "$PROJECT_ROOT/backups"
    
    log "Environnement configuré"
}

# Fonction pour installer les dépendances
install_dependencies() {
    log "Installation des dépendances..."
    
    # Backend Python
    if [ -f "$PROJECT_ROOT/backend/requirements.txt" ]; then
        info "Installation des dépendances Python..."
        cd "$PROJECT_ROOT/backend"
        pip3 install -r requirements.txt
    fi
    
    # Frontend Node.js
    if [ -f "$PROJECT_ROOT/frontend/package.json" ]; then
        info "Installation des dépendances Node.js..."
        cd "$PROJECT_ROOT/frontend"
        npm install
    fi
    
    # Blockchain
    if [ -f "$PROJECT_ROOT/blockchain/package.json" ]; then
        info "Installation des dépendances blockchain..."
        cd "$PROJECT_ROOT/blockchain"
        npm install
    fi
    
    log "Dépendances installées"
}

# Fonction pour déployer les smart contracts
deploy_contracts() {
    log "Déploiement des smart contracts..."
    
    cd "$PROJECT_ROOT/blockchain"
    
    # Compiler les contrats
    info "Compilation des smart contracts..."
    npx hardhat compile
    
    # Attendre que le nœud Hardhat soit prêt
    info "Attente du nœud Hardhat..."
    sleep 10
    
    # Déployer les contrats
    info "Déploiement des contrats..."
    npx hardhat run scripts/deploy.js --network local
    
    log "Smart contracts déployés"
}

# Fonction pour synchroniser le référentiel CCAM
sync_ccam() {
    log "Synchronisation du référentiel CCAM..."
    
    if [ -f "$PROJECT_ROOT/scripts/sync_ccam.sh" ]; then
        cd "$PROJECT_ROOT"
        ./scripts/sync_ccam.sh
    else
        warn "Script de synchronisation CCAM non trouvé"
    fi
}

# Fonction pour lancer les services
start_services() {
    log "Démarrage des services..."
    
    cd "$PROJECT_ROOT/infra/docker"
    
    # Lancer les services de base
    info "Démarrage des services de base (PostgreSQL, Redis, RabbitMQ)..."
    docker-compose up -d postgres redis rabbitmq
    
    # Attendre que les services soient prêts
    info "Attente de la disponibilité des services..."
    sleep 15
    
    # Lancer le nœud blockchain
    info "Démarrage du nœud blockchain..."
    docker-compose up -d hardhat
    
    # Attendre que le nœud soit prêt
    sleep 10
    
    # Déployer les contrats
    deploy_contracts
    
    # Lancer le backend
    info "Démarrage du backend..."
    docker-compose up -d backend
    
    # Attendre que le backend soit prêt
    sleep 10
    
    # Lancer le frontend
    info "Démarrage du frontend..."
    docker-compose up -d frontend
    
    # Lancer les workers
    info "Démarrage des workers IA..."
    docker-compose up -d ai_worker celery_beat
    
    log "Tous les services sont démarrés"
}

# Fonction pour vérifier le statut des services
check_status() {
    log "Vérification du statut des services..."
    
    cd "$PROJECT_ROOT/infra/docker"
    
    # Vérifier les conteneurs
    docker-compose ps
    
    # Vérifier les endpoints
    info "Vérification des endpoints..."
    
    # Backend
    if curl -f http://localhost:8000/health &> /dev/null; then
        log "✓ Backend accessible"
    else
        warn "✗ Backend non accessible"
    fi
    
    # Frontend
    if curl -f http://localhost:3000 &> /dev/null; then
        log "✓ Frontend accessible"
    else
        warn "✗ Frontend non accessible"
    fi
    
    # Blockchain
    if curl -f -X POST -H "Content-Type: application/json" \
        --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
        http://localhost:8545 &> /dev/null; then
        log "✓ Blockchain accessible"
    else
        warn "✗ Blockchain non accessible"
    fi
}

# Fonction pour afficher les informations d'accès
show_access_info() {
    log "=== INFORMATIONS D'ACCÈS ==="
    echo ""
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📊 API Documentation: http://localhost:8000/docs"
    echo "🔗 Blockchain: http://localhost:8545"
    echo "📈 Prometheus: http://localhost:9090"
    echo "📊 Grafana: http://localhost:3001 (admin/admin)"
    echo "🐰 RabbitMQ: http://localhost:15672 (guest/guest)"
    echo ""
    echo "📁 Logs: $PROJECT_ROOT/logs"
    echo "📁 Données: $PROJECT_ROOT/data"
    echo ""
    echo "🛠️  Commandes utiles:"
    echo "  - Arrêter: docker-compose down"
    echo "  - Logs: docker-compose logs -f [service]"
    echo "  - Redémarrer: docker-compose restart [service]"
    echo ""
}

# Fonction pour nettoyer
cleanup() {
    log "Nettoyage..."
    
    cd "$PROJECT_ROOT/infra/docker"
    
    # Arrêter tous les services
    docker-compose down
    
    # Supprimer les volumes si demandé
    if [ "$1" = "--clean" ]; then
        warn "Suppression des volumes (données perdues)..."
        docker-compose down -v
    fi
    
    log "Nettoyage terminé"
}

# Fonction d'aide
show_help() {
    echo "Usage: $0 [COMMANDE]"
    echo ""
    echo "Commandes:"
    echo "  start       Démarre l'application complète"
    echo "  stop        Arrête tous les services"
    echo "  restart     Redémarre tous les services"
    echo "  status      Affiche le statut des services"
    echo "  logs        Affiche les logs en temps réel"
    echo "  clean       Arrête et nettoie les volumes"
    echo "  setup       Configure l'environnement initial"
    echo "  help        Affiche cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 start    # Démarre l'application"
    echo "  $0 status   # Vérifie le statut"
    echo "  $0 clean    # Nettoie complètement"
}

# Fonction principale
main() {
    case "${1:-start}" in
        "start")
            check_prerequisites
            setup_environment
            install_dependencies
            start_services
            check_status
            show_access_info
            ;;
        "stop")
            cd "$PROJECT_ROOT/infra/docker"
            docker-compose down
            log "Services arrêtés"
            ;;
        "restart")
            cd "$PROJECT_ROOT/infra/docker"
            docker-compose restart
            log "Services redémarrés"
            ;;
        "status")
            check_status
            ;;
        "logs")
            cd "$PROJECT_ROOT/infra/docker"
            docker-compose logs -f
            ;;
        "clean")
            cleanup --clean
            ;;
        "setup")
            check_prerequisites
            setup_environment
            install_dependencies
            log "Configuration initiale terminée"
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            error "Commande inconnue: $1"
            show_help
            exit 1
            ;;
    esac
}

# Gestion des erreurs
trap 'error "Erreur survenue à la ligne $LINENO. Arrêt du script."; exit 1' ERR

# Exécution du script
main "$@"