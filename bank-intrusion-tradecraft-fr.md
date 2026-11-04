# COMMENT LES ACTEURS MALVEILLANTS COMPROMETTENT LES BANQUES

*Accès initial, phase de résidence et mouvement de l'argent — l'anatomie d'une intrusion bancaire*

## Table of contents

- [LES TROIS PORTES D'ENTRÉE](#les-trois-portes-dentrée)
  - [1. Les gens (accès initial)](#1-les-gens-accès-initial)
  - [2. Le périmètre (technique)](#2-le-périmètre-technique)
  - [3. Le mouvement de l'argent (l'objectif réel)](#3-le-mouvement-de-largent-lobjectif-réel)
- [LA PHASE DE RÉSIDENCE — OÙ SE TROUVE LA COMPÉTENCE](#la-phase-de-résidence--où-se-trouve-la-compétence)
- [L'ANGLE INITIÉ](#langle-initié)
- [LA SORTIE](#la-sortie)
- [CE QUI LES ARRÊTE VRAIMENT](#ce-qui-les-arrête-vraiment)

## LES TROIS PORTES D'ENTRÉE

### 1. Les gens (accès initial)

- **Hameçonnage / hameçonnage ciblé** — le grand classique. Pas le « cliquez sur ce lien » bas de gamme ; les groupes modernes font du *thread hijacking* : ils compromettent la boîte mail d'un fournisseur et répondent à l'intérieur d'un fil de facturation existant avec un IBAN remplacé. Pas de pièce jointe, pas de lien, rien que la passerelle puisse signaler.
- **Fatigue MFA / push bombing** — spammer des notifications push Okta/Azure à 2h du matin jusqu'à ce que quelqu'un approuve. Combiné à un mot de passe volé dans un journal d'infostealer, c'est *le* vecteur dominant 2023–2026 (tout le playbook de Scattered Spider).
- **Ingénierie sociale au support** — appeler le service desk en se faisant passer pour un employé, répondre aux questions de sécurité (souvent récoltées sur LinkedIn + fuites de données), obtenir une réinitialisation MFA. SIM swap pour le facteur SMS.
- **Vishing + AiTM** — l'attaquant au téléphone pendant qu'un kit de reverse-proxy (classe Evilginx) se place entre la victime et la vraie page de connexion, volant le cookie de session. Le MFA est satisfait ; le cookie est rejoué.
- **Tiers / chaîne d'approvisionnement** — MSP, éditeur de core banking, processeur de paiement, ou une appliance de transfert de fichiers. Un petit fournisseur mal sécurisé ouvre un tunnel vers vingt banques (voir : Accellion FTA, MOVEit, Cl0p).

### 2. Le périmètre (technique)

- **Exploitation d'équipements de bordure** — appliances VPN, Citrix, Fortinet, Ivanti, Exchange. Une RCE pré-auth sur une box exposée à Internet, c'est l'entrée la plus propre qui existe. Pas d'utilisateur à duper.
- **Services exposés** — RDP/VNC/SSH sur la mauvaise interface, Jenkins, vieux Tomcat, IIS non patché. Shodan fait la reconnaissance gratuitement.
- **Failles applicatives web** — SQLi, IDOR, SSRF vers le réseau interne depuis le portail de banque en ligne lui-même.
- **Credential stuffing** contre les portails clients, puis pivot via un mot de passe employé réutilisé.

### 3. Le mouvement de l'argent (l'objectif réel)

C'est ce qui sépare les groupes « banque » des groupes « rançongiciel » — ils ne veulent pas chiffrer, ils veulent *autoriser des virements*.

- **Compromission SWIFT / commutateur de paiement** — le schéma Bangladesh Bank : entrer, étudier le workflow de l'opérateur pendant des semaines, puis soumettre de faux messages MT103 pendant une fenêtre de jours fériés. Spécialité du groupe Lazarus. Le plus dur n'est pas le piratage, c'est de déjouer la réconciliation et les contrôles de la banque correspondante.
- **Jackpotting de DAB / cash-out** — soit logique (malware sur le DAB, ou un C2 qui ordonne la distribution), soit physique avec une « black box ». Nécessite généralement un initié ou un accès physique.
- **Compromission d'émetteur / processeur de cartes** — voler les PAN chez le processeur, revendre en gros, ou cloner et encaisser via des mules.
- **Fraude au virement (BEC)** — aucun malware. Juste un mail convaincant du « directeur financier » à l'équipe trésorerie, ou une boîte fournisseur compromise. Meilleur retour sur investissement de tout le domaine.
- **Réseaux de mules** — recrutées via des annonces « agent de transfert d'argent », des étudiants, ou du blanchiment crypto. Le moteur antifraude de la banque voit des titulaires de comptes légitimes recevoir et réexpédier des fonds.

## LA PHASE DE RÉSIDENCE — OÙ SE TROUVE LA COMPÉTENCE

Ce que les rapports montrent systématiquement : **des semaines à des mois à l'intérieur avant de toucher l'argent.**

- **Reconnaissance** — énumération AD interne (BloodHound), cartographie de qui approuve les virements, quel est le poste trésorerie, où se trouve le terminal SWIFT, les plannings d'équipe.
- **Élévation de privilèges** — Kerberoasting, abus d'ADCS, abus de GPO, dump de LSASS, vol de tokens.
- **Mouvement latéral** — RDP, SMB, WMI, PsExec, ou simplement *living off the land* avec des binaires signés.
- **Persistance** — tâches planifiées, services, contrôleurs de domaine pirates, comptes VPN backdoorés, parfois un implant matériel.
- **Évasion défensive** — désactiver ou aveugler l'EDR, effacer les logs, utiliser les outils d'admin de la banque pour que le trafic paraisse normal, opérer aux heures ouvrables locales de la cible pour se fondre.

## L'ANGLE INITIÉ

Ne jamais le sous-estimer. Un guichetier, un DBA, un prestataire avec un compte obsolète. Parfois c'est de la coercition (enlèvement de membre de la famille, l'« enlèvement express » est un vrai schéma dans certaines régions d'Amérique latine), parfois juste de la cupidité. L'intrusion technique ne fait souvent que *soutenir* un initié capable d'approuver le virement.

## LA SORTIE

- Superposition via banques correspondantes, ponts crypto, ou blanchiment basé sur le commerce (fausses factures, sur/sous-facturation).
- Parfois le groupe *fait* détoner un rançongiciel ensuite comme couverture — le bruit du chiffrement enterre la fraude au virement dans le chaos de la réponse à incident.

## CE QUI LES ARRÊTE VRAIMENT

- MFA résistant au hameçonnage (FIDO2/passkeys) tue d'emblée les classes AiTM et push-bombing.
- Segmentation réseau entre l'IT corporate et la zone paiement/SWIFT — la plupart des gros braquages sont morts à ce mur.
- Vérification hors bande pour tout changement de coordonnées de paiement (appeler le numéro connu, pas celui du mail).
- Surveillance agressive de l'*authentification*, pas seulement des malwares — impossible travel, nouvel appareil + reset MFA dans la même heure, schémas de reset au support.
- Accès tiers revus comme ton propre réseau, parce que c'en est un.
