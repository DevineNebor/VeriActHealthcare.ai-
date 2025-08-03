const { ethers } = require("hardhat");

async function main() {
  console.log("🚀 Déploiement du contrat CCAMRegistry...");

  // Récupérer le compte de déploiement
  const [deployer] = await ethers.getSigners();
  console.log("📝 Déploiement avec le compte:", deployer.address);
  console.log("💰 Balance du compte:", ethers.formatEther(await deployer.provider.getBalance(deployer.address)), "ETH");

  // Déployer le contrat CCAMRegistry
  const CCAMRegistry = await ethers.getContractFactory("CCAMRegistry");
  const ccamRegistry = await CCAMRegistry.deploy();
  await ccamRegistry.waitForDeployment();

  const contractAddress = await ccamRegistry.getAddress();
  console.log("✅ CCAMRegistry déployé à l'adresse:", contractAddress);

  // Vérifier les rôles par défaut
  const DEFAULT_ADMIN_ROLE = await ccamRegistry.DEFAULT_ADMIN_ROLE();
  const VALIDATOR_ROLE = await ccamRegistry.VALIDATOR_ROLE();
  const OVERRIDE_ROLE = await ccamRegistry.OVERRIDE_ROLE();
  const AUDIT_ROLE = await ccamRegistry.AUDIT_ROLE();

  console.log("🔐 Rôles configurés:");
  console.log("  - DEFAULT_ADMIN_ROLE:", DEFAULT_ADMIN_ROLE);
  console.log("  - VALIDATOR_ROLE:", VALIDATOR_ROLE);
  console.log("  - OVERRIDE_ROLE:", OVERRIDE_ROLE);
  console.log("  - AUDIT_ROLE:", AUDIT_ROLE);

  // Vérifier que le déployeur a tous les rôles
  const hasAdminRole = await ccamRegistry.hasRole(DEFAULT_ADMIN_ROLE, deployer.address);
  const hasValidatorRole = await ccamRegistry.hasRole(VALIDATOR_ROLE, deployer.address);
  const hasOverrideRole = await ccamRegistry.hasRole(OVERRIDE_ROLE, deployer.address);
  const hasAuditRole = await ccamRegistry.hasRole(AUDIT_ROLE, deployer.address);

  console.log("👤 Rôles du déployeur:");
  console.log("  - Admin:", hasAdminRole);
  console.log("  - Validator:", hasValidatorRole);
  console.log("  - Override:", hasOverrideRole);
  console.log("  - Audit:", hasAuditRole);

  // Enregistrer une version de test du référentiel CCAM
  console.log("📚 Enregistrement d'une version de test du référentiel CCAM...");
  
  const testVersion = "2024.1";
  const testNom = "CCAM 2024 - Version 1";
  const testChecksum = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef";
  const testDateEffet = Math.floor(Date.now() / 1000); // Maintenant
  const testDateFin = 0; // Pas de date de fin

  try {
    const tx = await ccamRegistry.registerVersion(
      testVersion,
      testNom,
      testChecksum,
      testDateEffet,
      testDateFin
    );
    await tx.wait();
    console.log("✅ Version de test enregistrée:", testVersion);
  } catch (error) {
    console.error("❌ Erreur lors de l'enregistrement de la version de test:", error.message);
  }

  // Test d'enregistrement d'un acte
  console.log("🏥 Test d'enregistrement d'un acte...");
  
  const testNumeroActe = "ACTE-2024-001";
  const testPatientId = "PAT-12345";
  const testCodeCCAM = "HHFA001";
  const testVersionCCAM = "2024.1";
  const testJustification = "Test d'enregistrement d'acte";

  try {
    const tx = await ccamRegistry.registerActe(
      testNumeroActe,
      testPatientId,
      testCodeCCAM,
      testVersionCCAM,
      testJustification
    );
    const receipt = await tx.wait();
    console.log("✅ Acte de test enregistré:", testNumeroActe);
    console.log("📋 Transaction hash:", receipt.hash);
  } catch (error) {
    console.error("❌ Erreur lors de l'enregistrement de l'acte de test:", error.message);
  }

  // Afficher les informations de déploiement
  console.log("\n🎉 Déploiement terminé avec succès!");
  console.log("=".repeat(50));
  console.log("📋 Informations de déploiement:");
  console.log("  - Contrat: CCAMRegistry");
  console.log("  - Adresse:", contractAddress);
  console.log("  - Réseau:", network.name);
  console.log("  - Déployeur:", deployer.address);
  console.log("=".repeat(50));

  // Sauvegarder les informations de déploiement
  const deploymentInfo = {
    contract: "CCAMRegistry",
    address: contractAddress,
    network: network.name,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    roles: {
      DEFAULT_ADMIN_ROLE,
      VALIDATOR_ROLE,
      OVERRIDE_ROLE,
      AUDIT_ROLE
    }
  };

  // Écrire dans un fichier pour utilisation par le backend
  const fs = require("fs");
  const path = require("path");
  
  const deploymentPath = path.join(__dirname, "..", "deployment.json");
  fs.writeFileSync(deploymentPath, JSON.stringify(deploymentInfo, null, 2));
  console.log("💾 Informations de déploiement sauvegardées dans:", deploymentPath);

  return {
    contractAddress,
    deploymentInfo
  };
}

// Fonction pour ajouter des rôles à d'autres adresses
async function addRoles(contractAddress, userAddress, roles) {
  const CCAMRegistry = await ethers.getContractFactory("CCAMRegistry");
  const ccamRegistry = CCAMRegistry.attach(contractAddress);

  for (const role of roles) {
    try {
      const tx = await ccamRegistry.grantRole(role, userAddress);
      await tx.wait();
      console.log(`✅ Rôle ${role} accordé à ${userAddress}`);
    } catch (error) {
      console.error(`❌ Erreur lors de l'attribution du rôle ${role}:`, error.message);
    }
  }
}

// Fonction pour récupérer les informations du contrat
async function getContractInfo(contractAddress) {
  const CCAMRegistry = await ethers.getContractFactory("CCAMRegistry");
  const ccamRegistry = CCAMRegistry.attach(contractAddress);

  const totalActes = await ccamRegistry.getTotalActes();
  const totalOverrides = await ccamRegistry.getTotalOverrides();
  const totalVersions = await ccamRegistry.getTotalVersions();

  console.log("📊 Statistiques du contrat:");
  console.log("  - Total actes:", totalActes.toString());
  console.log("  - Total overrides:", totalOverrides.toString());
  console.log("  - Total versions:", totalVersions.toString());

  return {
    totalActes: totalActes.toString(),
    totalOverrides: totalOverrides.toString(),
    totalVersions: totalVersions.toString()
  };
}

// Exporter les fonctions pour utilisation dans d'autres scripts
module.exports = {
  main,
  addRoles,
  getContractInfo
};

// Exécuter le déploiement si le script est appelé directement
if (require.main === module) {
  main()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error("❌ Erreur lors du déploiement:", error);
      process.exit(1);
    });
}