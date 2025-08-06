#!/usr/bin/env python3
"""
Script de test pour valider l'installation de CCAM AI + Blockchain
Vérifie que tous les composants sont correctement installés et configurés
"""

import sys
import os
import json
import subprocess
import requests
import time
from pathlib import Path
from typing import Dict, List, Any

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class InstallationTester:
    """Classe pour tester l'installation complète"""
    
    def __init__(self):
        self.project_root = project_root
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Afficher un message de log"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_passed(self, test_name: str, details: str = ""):
        """Marquer un test comme réussi"""
        self.results["passed"].append({"test": test_name, "details": details})
        self.log(f"✓ {test_name}", "PASS")
        if details:
            self.log(f"  {details}", "INFO")
    
    def test_failed(self, test_name: str, error: str = ""):
        """Marquer un test comme échoué"""
        self.results["failed"].append({"test": test_name, "error": error})
        self.log(f"✗ {test_name}", "FAIL")
        if error:
            self.log(f"  Erreur: {error}", "ERROR")
    
    def test_warning(self, test_name: str, warning: str = ""):
        """Marquer un avertissement"""
        self.results["warnings"].append({"test": test_name, "warning": warning})
        self.log(f"⚠ {test_name}", "WARN")
        if warning:
            self.log(f"  Avertissement: {warning}", "WARN")
    
    def test_file_structure(self):
        """Tester la structure des fichiers"""
        self.log("Test de la structure des fichiers...")
        
        required_dirs = [
            "backend",
            "frontend", 
            "blockchain",
            "agent_ai",
            "infra",
            "docs",
            "tests",
            "scripts"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                self.test_passed(f"Répertoire {dir_name} existe")
            else:
                self.test_failed(f"Répertoire {dir_name} manquant")
        
        # Vérifier les fichiers importants
        important_files = [
            "README.md",
            ".env.example",
            "backend/requirements.txt",
            "frontend/package.json",
            "blockchain/package.json",
            "infra/docker/docker-compose.yml"
        ]
        
        for file_path in important_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.test_passed(f"Fichier {file_path} existe")
            else:
                self.test_failed(f"Fichier {file_path} manquant")
    
    def test_python_dependencies(self):
        """Tester les dépendances Python"""
        self.log("Test des dépendances Python...")
        
        try:
            import fastapi
            self.test_passed("FastAPI installé", f"Version: {fastapi.__version__}")
        except ImportError:
            self.test_failed("FastAPI non installé")
        
        try:
            import sqlalchemy
            self.test_passed("SQLAlchemy installé", f"Version: {sqlalchemy.__version__}")
        except ImportError:
            self.test_failed("SQLAlchemy non installé")
        
        try:
            import openai
            self.test_passed("OpenAI installé", f"Version: {openai.__version__}")
        except ImportError:
            self.test_failed("OpenAI non installé")
        
        try:
            import web3
            self.test_passed("Web3 installé", f"Version: {web3.__version__}")
        except ImportError:
            self.test_failed("Web3 non installé")
    
    def test_node_dependencies(self):
        """Tester les dépendances Node.js"""
        self.log("Test des dépendances Node.js...")
        
        # Vérifier que Node.js est installé
        try:
            result = subprocess.run(["node", "--version"], 
                                  capture_output=True, text=True, check=True)
            self.test_passed("Node.js installé", f"Version: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.test_failed("Node.js non installé")
        
        # Vérifier que npm est installé
        try:
            result = subprocess.run(["npm", "--version"], 
                                  capture_output=True, text=True, check=True)
            self.test_passed("npm installé", f"Version: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.test_failed("npm non installé")
    
    def test_docker(self):
        """Tester Docker"""
        self.log("Test de Docker...")
        
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, check=True)
            self.test_passed("Docker installé", f"Version: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.test_failed("Docker non installé")
        
        try:
            result = subprocess.run(["docker-compose", "--version"], 
                                  capture_output=True, text=True, check=True)
            self.test_passed("Docker Compose installé", f"Version: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.test_failed("Docker Compose non installé")
    
    def test_environment_file(self):
        """Tester le fichier d'environnement"""
        self.log("Test du fichier d'environnement...")
        
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"
        
        if env_file.exists():
            self.test_passed("Fichier .env existe")
            
            # Vérifier quelques variables importantes
            with open(env_file, 'r') as f:
                content = f.read()
                
            required_vars = [
                "DATABASE_URL",
                "REDIS_URL", 
                "LLM_API_KEY",
                "SECRET_KEY",
                "JWT_SECRET_KEY"
            ]
            
            for var in required_vars:
                if var in content:
                    self.test_passed(f"Variable {var} configurée")
                else:
                    self.test_warning(f"Variable {var} non configurée")
        else:
            if env_example.exists():
                self.test_warning("Fichier .env manquant", "Copiez .env.example vers .env")
            else:
                self.test_failed("Fichiers .env et .env.example manquants")
    
    def test_backend_structure(self):
        """Tester la structure du backend"""
        self.log("Test de la structure du backend...")
        
        backend_dir = self.project_root / "backend"
        
        if not backend_dir.exists():
            self.test_failed("Répertoire backend manquant")
            return
        
        # Vérifier les modules principaux
        modules = [
            "app",
            "app/api",
            "app/models", 
            "app/services",
            "app/schemas"
        ]
        
        for module in modules:
            module_path = backend_dir / module
            if module_path.exists():
                self.test_passed(f"Module backend {module} existe")
            else:
                self.test_failed(f"Module backend {module} manquant")
    
    def test_blockchain_structure(self):
        """Tester la structure blockchain"""
        self.log("Test de la structure blockchain...")
        
        blockchain_dir = self.project_root / "blockchain"
        
        if not blockchain_dir.exists():
            self.test_failed("Répertoire blockchain manquant")
            return
        
        # Vérifier les fichiers importants
        files = [
            "contracts/CCAMRegistry.sol",
            "scripts/deploy.js",
            "hardhat.config.js",
            "package.json"
        ]
        
        for file_path in files:
            full_path = blockchain_dir / file_path
            if full_path.exists():
                self.test_passed(f"Fichier blockchain {file_path} existe")
            else:
                self.test_failed(f"Fichier blockchain {file_path} manquant")
    
    def test_frontend_structure(self):
        """Tester la structure du frontend"""
        self.log("Test de la structure du frontend...")
        
        frontend_dir = self.project_root / "frontend"
        
        if not frontend_dir.exists():
            self.test_failed("Répertoire frontend manquant")
            return
        
        # Vérifier les fichiers importants
        files = [
            "package.json",
            "public/index.html"
        ]
        
        for file_path in files:
            full_path = frontend_dir / file_path
            if full_path.exists():
                self.test_passed(f"Fichier frontend {file_path} existe")
            else:
                self.test_failed(f"Fichier frontend {file_path} manquant")
    
    def test_scripts(self):
        """Tester les scripts"""
        self.log("Test des scripts...")
        
        scripts_dir = self.project_root / "scripts"
        
        if not scripts_dir.exists():
            self.test_failed("Répertoire scripts manquant")
            return
        
        # Vérifier les scripts importants
        scripts = [
            "sync_ccam.sh",
            "quick-start.sh"
        ]
        
        for script in scripts:
            script_path = scripts_dir / script
            if script_path.exists():
                if os.access(script_path, os.X_OK):
                    self.test_passed(f"Script {script} existe et est exécutable")
                else:
                    self.test_warning(f"Script {script} existe mais n'est pas exécutable")
            else:
                self.test_failed(f"Script {script} manquant")
    
    def test_docker_compose(self):
        """Tester Docker Compose"""
        self.log("Test de Docker Compose...")
        
        compose_file = self.project_root / "infra" / "docker" / "docker-compose.yml"
        
        if not compose_file.exists():
            self.test_failed("Fichier docker-compose.yml manquant")
            return
        
        # Vérifier que le fichier est valide
        try:
            with open(compose_file, 'r') as f:
                content = f.read()
                
            if "version:" in content and "services:" in content:
                self.test_passed("Fichier docker-compose.yml valide")
            else:
                self.test_failed("Fichier docker-compose.yml invalide")
        except Exception as e:
            self.test_failed(f"Erreur lors de la lecture du docker-compose.yml: {e}")
    
    def test_services_connectivity(self):
        """Tester la connectivité des services (si démarrés)"""
        self.log("Test de la connectivité des services...")
        
        services = [
            ("Backend", "http://localhost:8000/health"),
            ("Frontend", "http://localhost:3000"),
            ("Blockchain", "http://localhost:8545"),
            ("Prometheus", "http://localhost:9090"),
            ("Grafana", "http://localhost:3001")
        ]
        
        for service_name, url in services:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.test_passed(f"Service {service_name} accessible", f"URL: {url}")
                else:
                    self.test_warning(f"Service {service_name} répond avec code {response.status_code}")
            except requests.exceptions.RequestException:
                self.test_warning(f"Service {service_name} non accessible", f"URL: {url}")
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        self.log("=== DÉBUT DES TESTS D'INSTALLATION ===")
        
        # Tests de structure
        self.test_file_structure()
        self.test_backend_structure()
        self.test_blockchain_structure()
        self.test_frontend_structure()
        
        # Tests de dépendances
        self.test_python_dependencies()
        self.test_node_dependencies()
        self.test_docker()
        
        # Tests de configuration
        self.test_environment_file()
        self.test_scripts()
        self.test_docker_compose()
        
        # Tests de connectivité (optionnels)
        self.test_services_connectivity()
        
        # Résumé
        self.print_summary()
    
    def print_summary(self):
        """Afficher le résumé des tests"""
        self.log("=== RÉSUMÉ DES TESTS ===")
        
        total_tests = len(self.results["passed"]) + len(self.results["failed"]) + len(self.results["warnings"])
        
        print(f"\n📊 Statistiques:")
        print(f"  Total: {total_tests} tests")
        print(f"  ✓ Réussis: {len(self.results['passed'])}")
        print(f"  ✗ Échoués: {len(self.results['failed'])}")
        print(f"  ⚠ Avertissements: {len(self.results['warnings'])}")
        
        if self.results["failed"]:
            print(f"\n❌ Tests échoués:")
            for test in self.results["failed"]:
                print(f"  - {test['test']}: {test['error']}")
        
        if self.results["warnings"]:
            print(f"\n⚠️ Avertissements:")
            for test in self.results["warnings"]:
                print(f"  - {test['test']}: {test['warning']}")
        
        if not self.results["failed"]:
            print(f"\n🎉 Tous les tests critiques sont passés!")
            print(f"L'installation semble correcte.")
        else:
            print(f"\n🔧 Veuillez corriger les erreurs avant de continuer.")
        
        # Sauvegarder les résultats
        results_file = self.project_root / "tests" / "installation_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Résultats détaillés sauvegardés dans: {results_file}")

def main():
    """Fonction principale"""
    tester = InstallationTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()