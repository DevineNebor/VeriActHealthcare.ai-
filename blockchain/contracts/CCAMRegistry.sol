// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title CCAMRegistry
 * @dev Smart contract pour l'enregistrement immuable des actes CCAM
 * Gère la validation, les overrides, et l'audit trail
 */
contract CCAMRegistry is AccessControl, ReentrancyGuard {
    using Counters for Counters.Counter;

    // Rôles
    bytes32 public constant VALIDATOR_ROLE = keccak256("VALIDATOR_ROLE");
    bytes32 public constant OVERRIDE_ROLE = keccak256("OVERRIDE_ROLE");
    bytes32 public constant AUDIT_ROLE = keccak256("AUDIT_ROLE");

    // Compteurs
    Counters.Counter private _acteIds;
    Counters.Counter private _overrideIds;
    Counters.Counter private _versionIds;

    // Structures de données
    struct Acte {
        uint256 acteId;
        string numeroActe;
        string patientId; // ID pseudonymisé
        string codeCCAM;
        string versionCCAM;
        uint256 timestamp;
        address auteur;
        string justification;
        bool isValidated;
        bool isRejected;
        string rejectionReason;
    }

    struct Override {
        uint256 overrideId;
        uint256 acteId;
        string codeCCAMOriginal;
        string codeCCAMOverride;
        uint256 timestamp;
        address auteur;
        string justification;
        string signatureNumerique;
        bool isApproved;
        address approvedBy;
    }

    struct VersionRef {
        uint256 versionId;
        string version;
        string nom;
        string checksum;
        uint256 dateEffet;
        uint256 dateFin;
        bool isActive;
        bool isDeprecated;
    }

    struct AuditEntry {
        uint256 acteId;
        string action;
        string entityType;
        uint256 entityId;
        uint256 timestamp;
        address utilisateur;
        string oldValues;
        string newValues;
        string transactionHash;
    }

    // Mappings
    mapping(uint256 => Acte) public actes;
    mapping(uint256 => Override) public overrides;
    mapping(uint256 => VersionRef) public versions;
    mapping(uint256 => AuditEntry[]) public auditTrail;
    mapping(string => uint256) public acteByNumero;
    mapping(string => uint256) public versionByCode;

    // Événements
    event ActeRegistered(
        uint256 indexed acteId,
        string numeroActe,
        string patientId,
        string codeCCAM,
        address indexed auteur,
        uint256 timestamp
    );

    event ActeValidated(
        uint256 indexed acteId,
        string codeCCAM,
        address indexed validateur,
        uint256 timestamp
    );

    event ActeRejected(
        uint256 indexed acteId,
        string reason,
        address indexed rejeteur,
        uint256 timestamp
    );

    event OverrideCreated(
        uint256 indexed overrideId,
        uint256 indexed acteId,
        string codeCCAMOriginal,
        string codeCCAMOverride,
        address indexed auteur,
        uint256 timestamp
    );

    event OverrideApproved(
        uint256 indexed overrideId,
        address indexed approbateur,
        uint256 timestamp
    );

    event VersionRegistered(
        uint256 indexed versionId,
        string version,
        string nom,
        uint256 dateEffet,
        bool isActive
    );

    event AuditEntryCreated(
        uint256 indexed acteId,
        string action,
        address indexed utilisateur,
        uint256 timestamp
    );

    // Modifiers
    modifier onlyValidator() {
        require(hasRole(VALIDATOR_ROLE, msg.sender), "CCAMRegistry: Validator role required");
        _;
    }

    modifier onlyOverride() {
        require(hasRole(OVERRIDE_ROLE, msg.sender), "CCAMRegistry: Override role required");
        _;
    }

    modifier onlyAudit() {
        require(hasRole(AUDIT_ROLE, msg.sender), "CCAMRegistry: Audit role required");
        _;
    }

    modifier acteExists(uint256 acteId) {
        require(actes[acteId].acteId != 0, "CCAMRegistry: Acte does not exist");
        _;
    }

    modifier acteNotValidated(uint256 acteId) {
        require(!actes[acteId].isValidated, "CCAMRegistry: Acte already validated");
        require(!actes[acteId].isRejected, "CCAMRegistry: Acte already rejected");
        _;
    }

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(VALIDATOR_ROLE, msg.sender);
        _grantRole(OVERRIDE_ROLE, msg.sender);
        _grantRole(AUDIT_ROLE, msg.sender);
    }

    /**
     * @dev Enregistrer un nouvel acte
     * @param numeroActe Numéro unique de l'acte
     * @param patientId ID pseudonymisé du patient
     * @param codeCCAM Code CCAM suggéré
     * @param versionCCAM Version du référentiel CCAM utilisée
     * @param justification Justification de la suggestion
     */
    function registerActe(
        string memory numeroActe,
        string memory patientId,
        string memory codeCCAM,
        string memory versionCCAM,
        string memory justification
    ) external onlyValidator nonReentrant returns (uint256) {
        require(bytes(numeroActe).length > 0, "CCAMRegistry: Numero acte cannot be empty");
        require(acteByNumero[numeroActe] == 0, "CCAMRegistry: Acte numero already exists");

        _acteIds.increment();
        uint256 acteId = _acteIds.current();

        Acte memory newActe = Acte({
            acteId: acteId,
            numeroActe: numeroActe,
            patientId: patientId,
            codeCCAM: codeCCAM,
            versionCCAM: versionCCAM,
            timestamp: block.timestamp,
            auteur: msg.sender,
            justification: justification,
            isValidated: false,
            isRejected: false,
            rejectionReason: ""
        });

        actes[acteId] = newActe;
        acteByNumero[numeroActe] = acteId;

        emit ActeRegistered(acteId, numeroActe, patientId, codeCCAM, msg.sender, block.timestamp);

        return acteId;
    }

    /**
     * @dev Valider un acte
     * @param acteId ID de l'acte à valider
     * @param codeCCAM Code CCAM final validé
     * @param justification Justification de la validation
     */
    function validateActe(
        uint256 acteId,
        string memory codeCCAM,
        string memory justification
    ) external onlyValidator acteExists(acteId) acteNotValidated(acteId) nonReentrant {
        Acte storage acte = actes[acteId];
        acte.codeCCAM = codeCCAM;
        acte.justification = justification;
        acte.isValidated = true;

        emit ActeValidated(acteId, codeCCAM, msg.sender, block.timestamp);
    }

    /**
     * @dev Rejeter un acte
     * @param acteId ID de l'acte à rejeter
     * @param reason Raison du rejet
     */
    function rejectActe(
        uint256 acteId,
        string memory reason
    ) external onlyValidator acteExists(acteId) acteNotValidated(acteId) nonReentrant {
        Acte storage acte = actes[acteId];
        acte.isRejected = true;
        acte.rejectionReason = reason;

        emit ActeRejected(acteId, reason, msg.sender, block.timestamp);
    }

    /**
     * @dev Créer un override (correction manuelle)
     * @param acteId ID de l'acte
     * @param codeCCAMOriginal Code CCAM original
     * @param codeCCAMOverride Code CCAM de correction
     * @param justification Justification de l'override
     * @param signatureNumerique Signature numérique de l'utilisateur
     */
    function createOverride(
        uint256 acteId,
        string memory codeCCAMOriginal,
        string memory codeCCAMOverride,
        string memory justification,
        string memory signatureNumerique
    ) external onlyOverride acteExists(acteId) acteNotValidated(acteId) nonReentrant returns (uint256) {
        _overrideIds.increment();
        uint256 overrideId = _overrideIds.current();

        Override memory newOverride = Override({
            overrideId: overrideId,
            acteId: acteId,
            codeCCAMOriginal: codeCCAMOriginal,
            codeCCAMOverride: codeCCAMOverride,
            timestamp: block.timestamp,
            auteur: msg.sender,
            justification: justification,
            signatureNumerique: signatureNumerique,
            isApproved: false,
            approvedBy: address(0)
        });

        overrides[overrideId] = newOverride;

        emit OverrideCreated(
            overrideId,
            acteId,
            codeCCAMOriginal,
            codeCCAMOverride,
            msg.sender,
            block.timestamp
        );

        return overrideId;
    }

    /**
     * @dev Approuver un override
     * @param overrideId ID de l'override à approuver
     */
    function approveOverride(
        uint256 overrideId
    ) external onlyValidator nonReentrant {
        require(overrides[overrideId].overrideId != 0, "CCAMRegistry: Override does not exist");
        require(!overrides[overrideId].isApproved, "CCAMRegistry: Override already approved");

        Override storage override = overrides[overrideId];
        override.isApproved = true;
        override.approvedBy = msg.sender;

        // Mettre à jour l'acte avec le nouveau code
        uint256 acteId = override.acteId;
        actes[acteId].codeCCAM = override.codeCCAMOverride;

        emit OverrideApproved(overrideId, msg.sender, block.timestamp);
    }

    /**
     * @dev Enregistrer une version de référentiel CCAM
     * @param version Code de version
     * @param nom Nom de la version
     * @param checksum Checksum du fichier de référence
     * @param dateEffet Date d'effet (timestamp)
     * @param dateFin Date de fin (timestamp, 0 si pas de fin)
     */
    function registerVersion(
        string memory version,
        string memory nom,
        string memory checksum,
        uint256 dateEffet,
        uint256 dateFin
    ) external onlyValidator nonReentrant returns (uint256) {
        require(bytes(version).length > 0, "CCAMRegistry: Version cannot be empty");
        require(versionByCode[version] == 0, "CCAMRegistry: Version already exists");

        _versionIds.increment();
        uint256 versionId = _versionIds.current();

        VersionRef memory newVersion = VersionRef({
            versionId: versionId,
            version: version,
            nom: nom,
            checksum: checksum,
            dateEffet: dateEffet,
            dateFin: dateFin,
            isActive: true,
            isDeprecated: false
        });

        versions[versionId] = newVersion;
        versionByCode[version] = versionId;

        emit VersionRegistered(versionId, version, nom, dateEffet, true);

        return versionId;
    }

    /**
     * @dev Créer une entrée d'audit
     * @param acteId ID de l'acte
     * @param action Type d'action
     * @param entityType Type d'entité
     * @param entityId ID de l'entité
     * @param oldValues Anciennes valeurs (JSON)
     * @param newValues Nouvelles valeurs (JSON)
     */
    function createAuditEntry(
        uint256 acteId,
        string memory action,
        string memory entityType,
        uint256 entityId,
        string memory oldValues,
        string memory newValues
    ) external onlyAudit acteExists(acteId) nonReentrant {
        AuditEntry memory entry = AuditEntry({
            acteId: acteId,
            action: action,
            entityType: entityType,
            entityId: entityId,
            timestamp: block.timestamp,
            utilisateur: msg.sender,
            oldValues: oldValues,
            newValues: newValues,
            transactionHash: ""
        });

        auditTrail[acteId].push(entry);

        emit AuditEntryCreated(acteId, action, msg.sender, block.timestamp);
    }

    // Fonctions de lecture

    /**
     * @dev Récupérer un acte par son ID
     */
    function getActe(uint256 acteId) external view returns (Acte memory) {
        require(actes[acteId].acteId != 0, "CCAMRegistry: Acte does not exist");
        return actes[acteId];
    }

    /**
     * @dev Récupérer un acte par son numéro
     */
    function getActeByNumero(string memory numeroActe) external view returns (Acte memory) {
        uint256 acteId = acteByNumero[numeroActe];
        require(acteId != 0, "CCAMRegistry: Acte not found");
        return actes[acteId];
    }

    /**
     * @dev Récupérer un override par son ID
     */
    function getOverride(uint256 overrideId) external view returns (Override memory) {
        require(overrides[overrideId].overrideId != 0, "CCAMRegistry: Override does not exist");
        return overrides[overrideId];
    }

    /**
     * @dev Récupérer tous les overrides d'un acte
     */
    function getOverridesByActe(uint256 acteId) external view returns (uint256[] memory) {
        uint256 count = 0;
        uint256[] memory temp = new uint256[](_overrideIds.current());
        
        for (uint256 i = 1; i <= _overrideIds.current(); i++) {
            if (overrides[i].acteId == acteId) {
                temp[count] = i;
                count++;
            }
        }
        
        uint256[] memory result = new uint256[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = temp[i];
        }
        
        return result;
    }

    /**
     * @dev Récupérer le trail d'audit d'un acte
     */
    function getAuditTrail(uint256 acteId) external view returns (AuditEntry[] memory) {
        return auditTrail[acteId];
    }

    /**
     * @dev Récupérer une version par son code
     */
    function getVersionByCode(string memory version) external view returns (VersionRef memory) {
        uint256 versionId = versionByCode[version];
        require(versionId != 0, "CCAMRegistry: Version not found");
        return versions[versionId];
    }

    /**
     * @dev Récupérer le nombre total d'actes
     */
    function getTotalActes() external view returns (uint256) {
        return _acteIds.current();
    }

    /**
     * @dev Récupérer le nombre total d'overrides
     */
    function getTotalOverrides() external view returns (uint256) {
        return _overrideIds.current();
    }

    /**
     * @dev Récupérer le nombre total de versions
     */
    function getTotalVersions() external view returns (uint256) {
        return _versionIds.current();
    }
}