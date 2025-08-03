#!/bin/bash

# Script de synchronisation du référentiel CCAM
# Télécharge et met à jour la nomenclature CCAM depuis les sources officielles

set -e

# Configuration
CCAM_VERSION="${CCAM_VERSION:-2024}"
CCAM_DATA_DIR="${CCAM_DATA_DIR:-./data/ccam}"
CCAM_API_URL="${CCAM_API_URL:-https://api.ameli.fr/ccam}"
BACKUP_DIR="${BACKUP_DIR:-./backups/ccam}"
LOG_FILE="${LOG_FILE:-./logs/ccam_sync.log}"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a "$LOG_FILE"
}

# Fonction pour créer les répertoires nécessaires
create_directories() {
    log "Création des répertoires nécessaires..."
    
    mkdir -p "$CCAM_DATA_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$(dirname "$LOG_FILE")"
    
    log "Répertoires créés avec succès"
}

# Fonction pour sauvegarder les données existantes
backup_existing_data() {
    if [ -d "$CCAM_DATA_DIR" ] && [ "$(ls -A "$CCAM_DATA_DIR")" ]; then
        log "Sauvegarde des données existantes..."
        
        BACKUP_NAME="ccam_backup_$(date +'%Y%m%d_%H%M%S').tar.gz"
        tar -czf "$BACKUP_DIR/$BACKUP_NAME" -C "$(dirname "$CCAM_DATA_DIR")" "$(basename "$CCAM_DATA_DIR")"
        
        log "Sauvegarde créée: $BACKUP_NAME"
    else
        info "Aucune donnée existante à sauvegarder"
    fi
}

# Fonction pour télécharger le référentiel CCAM
download_ccam_reference() {
    log "Téléchargement du référentiel CCAM version $CCAM_VERSION..."
    
    # URL du fichier CCAM (exemple - à adapter selon les sources réelles)
    CCAM_DOWNLOAD_URL="$CCAM_API_URL/version/$CCAM_VERSION/download"
    
    # Télécharger le fichier
    if curl -L -o "$CCAM_DATA_DIR/ccam_$CCAM_VERSION.zip" "$CCAM_DOWNLOAD_URL"; then
        log "Téléchargement réussi"
    else
        error "Échec du téléchargement depuis $CCAM_DOWNLOAD_URL"
        return 1
    fi
}

# Fonction pour extraire et traiter les données
process_ccam_data() {
    log "Traitement des données CCAM..."
    
    cd "$CCAM_DATA_DIR"
    
    # Extraire le fichier ZIP
    if unzip -q "ccam_$CCAM_VERSION.zip"; then
        log "Extraction réussie"
    else
        error "Échec de l'extraction du fichier ZIP"
        return 1
    fi
    
    # Convertir en format JSON si nécessaire
    if [ -f "ccam_$CCAM_VERSION.csv" ]; then
        log "Conversion CSV vers JSON..."
        python3 -c "
import csv
import json
import sys

def csv_to_json(csv_file, json_file):
    data = []
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append(row)
    
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

csv_to_json('ccam_$CCAM_VERSION.csv', 'ccam_$CCAM_VERSION.json')
"
        log "Conversion terminée"
    fi
    
    # Calculer le checksum
    if [ -f "ccam_$CCAM_VERSION.json" ]; then
        CHECKSUM=$(sha256sum "ccam_$CCAM_VERSION.json" | cut -d' ' -f1)
        echo "$CHECKSUM" > "ccam_$CCAM_VERSION.checksum"
        log "Checksum calculé: $CHECKSUM"
    fi
}

# Fonction pour valider les données
validate_ccam_data() {
    log "Validation des données CCAM..."
    
    if [ ! -f "$CCAM_DATA_DIR/ccam_$CCAM_VERSION.json" ]; then
        error "Fichier JSON CCAM introuvable"
        return 1
    fi
    
    # Vérifier la structure JSON
    if python3 -c "
import json
import sys

try:
    with open('$CCAM_DATA_DIR/ccam_$CCAM_VERSION.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        print('Erreur: Les données ne sont pas une liste')
        sys.exit(1)
    
    if len(data) == 0:
        print('Erreur: Aucune donnée trouvée')
        sys.exit(1)
    
    # Vérifier la structure des premiers éléments
    required_fields = ['code', 'libelle']
    for i, item in enumerate(data[:10]):
        if not isinstance(item, dict):
            print(f'Erreur: Élément {i} n\'est pas un objet')
            sys.exit(1)
        
        for field in required_fields:
            if field not in item:
                print(f'Erreur: Champ requis "{field}" manquant dans l\'élément {i}')
                sys.exit(1)
    
    print(f'Validation réussie: {len(data)} codes CCAM trouvés')
    
except Exception as e:
    print(f'Erreur de validation: {e}')
    sys.exit(1)
"; then
        log "Validation réussie"
    else
        error "Échec de la validation"
        return 1
    fi
}

# Fonction pour mettre à jour la base de données
update_database() {
    log "Mise à jour de la base de données..."
    
    # Appeler le script Python pour mettre à jour la DB
    if python3 -c "
import sys
import os
sys.path.append('$PWD/backend')

from app.services.ccam_service import CCAMService
from app.core.database import get_db

async def update_ccam_database():
    try:
        ccam_service = CCAMService()
        await ccam_service.sync_ccam_reference('$CCAM_DATA_DIR/ccam_$CCAM_VERSION.json')
        print('Base de données mise à jour avec succès')
    except Exception as e:
        print(f'Erreur lors de la mise à jour: {e}')
        sys.exit(1)

import asyncio
asyncio.run(update_ccam_database())
"; then
        log "Base de données mise à jour avec succès"
    else
        error "Échec de la mise à jour de la base de données"
        return 1
    fi
}

# Fonction pour nettoyer les fichiers temporaires
cleanup() {
    log "Nettoyage des fichiers temporaires..."
    
    cd "$CCAM_DATA_DIR"
    
    # Supprimer les fichiers ZIP et CSV
    rm -f "ccam_$CCAM_VERSION.zip"
    rm -f "ccam_$CCAM_VERSION.csv"
    
    # Garder seulement les fichiers JSON et checksum
    log "Nettoyage terminé"
}

# Fonction pour générer un rapport
generate_report() {
    log "Génération du rapport de synchronisation..."
    
    REPORT_FILE="$CCAM_DATA_DIR/sync_report_$(date +'%Y%m%d_%H%M%S').txt"
    
    {
        echo "=== RAPPORT DE SYNCHRONISATION CCAM ==="
        echo "Date: $(date)"
        echo "Version: $CCAM_VERSION"
        echo "Répertoire de données: $CCAM_DATA_DIR"
        echo ""
        
        if [ -f "ccam_$CCAM_VERSION.json" ]; then
            echo "=== STATISTIQUES ==="
            python3 -c "
import json
with open('ccam_$CCAM_VERSION.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f'Nombre total de codes: {len(data)}')
print(f'Taille du fichier: {len(json.dumps(data, ensure_ascii=False))} caractères')
"
        fi
        
        echo ""
        echo "=== FICHIERS CRÉÉS ==="
        ls -la "$CCAM_DATA_DIR" | grep "ccam_$CCAM_VERSION"
        
        echo ""
        echo "=== CHECKSUM ==="
        if [ -f "ccam_$CCAM_VERSION.checksum" ]; then
            cat "ccam_$CCAM_VERSION.checksum"
        fi
        
    } > "$REPORT_FILE"
    
    log "Rapport généré: $REPORT_FILE"
}

# Fonction principale
main() {
    log "=== DÉBUT DE LA SYNCHRONISATION CCAM ==="
    
    # Vérifier les prérequis
    if ! command -v curl &> /dev/null; then
        error "curl n'est pas installé"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        error "python3 n'est pas installé"
        exit 1
    fi
    
    # Exécuter les étapes
    create_directories
    backup_existing_data
    download_ccam_reference
    process_ccam_data
    validate_ccam_data
    update_database
    cleanup
    generate_report
    
    log "=== SYNCHRONISATION CCAM TERMINÉE AVEC SUCCÈS ==="
}

# Gestion des erreurs
trap 'error "Erreur survenue à la ligne $LINENO. Arrêt du script."; exit 1' ERR

# Exécution du script
main "$@"