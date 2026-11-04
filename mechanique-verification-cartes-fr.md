# MÉCANIQUE DE LA VÉRIFICATION DE CARTES — 3DS, AVS, DÉTECTION

*Comment fonctionnent réellement l'authentification, l'autorisation et la détection*

## Table of contents

- [AVERTISSEMENT DE LECTURE](#avertissement-de-lecture)
- [1. LES QUATRE COUCHES D'UNE VÉRIFICATION DE CARTE](#1-les-quatre-couches-dune-vérification-de-carte)
  - [a) Validation du numéro (Luhn)](#a-validation-du-numéro-luhn)
  - [b) BIN / IIN — les 6 à 8 premiers chiffres](#b-bin--iin--les-6-à-8-premiers-chiffres)
  - [c) Autorisation auprès de l'émetteur](#c-autorisation-auprès-de-lémetteur)
  - [d) Contrôles de risque du marchand](#d-contrôles-de-risque-du-marchand)
- [2. 3-D SECURE ET LA NOTION DE "NO VBV"](#2-3-d-secure-et-la-notion-de-no-vbv)
- [3. AVS ET CVV — LES DEUX AUTRES BARRIÈRES](#3-avs-et-cvv--les-deux-autres-barrières)
  - [AVS (Address Verification System)](#avs-address-verification-system)
  - [CVV / CVC2](#cvv--cvc2)
- [4. COMMENT LES PASSERELLES DÉTECTENT UN OUTIL DE TEST](#4-comment-les-passerelles-détectent-un-outil-de-test)
  - [Côté marchand / PSP (prestataire de paiement)](#côté-marchand--psp-prestataire-de-paiement)
  - [Côté réseau (Visa / Mastercard)](#côté-réseau-visa--mastercard)
- [5. CONCLUSION TECHNIQUE](#5-conclusion-technique)
- [6. CADRE LÉGAL (RAPPEL FACTUEL)](#6-cadre-légal-rappel-factuel)
- [7. PISTES DE RECHERCHE LÉGITIMES](#7-pistes-de-recherche-légitimes)

## AVERTISSEMENT DE LECTURE

Document d'analyse défensive. Décrit comment fonctionnent l'authentification et la détection, pas comment contourner un système réel.

---

## 1. LES QUATRE COUCHES D'UNE VÉRIFICATION DE CARTE

Quand une carte est "testée" contre une passerelle de paiement, quatre contrôles distincts s'exécutent, dans cet ordre.

### a) Validation du numéro (Luhn)

Le dernier chiffre de la carte est une somme de contrôle calculée sur les autres chiffres. Cela élimine les numéros mal saisis ou générés au hasard. **Cela ne dit rien sur l'existence réelle de la carte.** Un outil qui "valide" par Luhn ne valide rien — il vérifie juste un format.

### b) BIN / IIN — les 6 à 8 premiers chiffres

Le BIN (*Bank Identification Number*, aussi IIN) identifie :

- l'émetteur (la banque) ;
- le pays d'émission ;
- le type de carte (crédit, débit, prépayée) ;
- le segment (classic, gold, business, etc.).

C'est la **seule information réellement disponible hors ligne**. C'est pourquoi les outils de tri regroupent les cartes par BIN : ils cherchent des émetteurs dont les contrôles sont réputés faibles. Mais un BIN "faible" n'est pas une carte utilisable — seulement une carte *peut-être* non bloquée.

### c) Autorisation auprès de l'émetteur

La vraie vérification. Le marchand envoie une demande d'autorisation qui transite par le réseau (Visa / Mastercard) jusqu'à la banque émettrice. La réponse est l'une des trois :

- **approuvée** — la transaction est autorisée ;
- **refusée** — solde insuffisant, carte bloquée, données incorrectes ;
- **referral** — l'émetteur demande une vérification supplémentaire.

C'est ici qu'interviennent le solde, l'état de la carte, les blocages antifraude et les plafonds. Aucun outil ne peut simuler cette étape : elle se déroule du côté de la banque.

### d) Contrôles de risque du marchand

AVS, CVV, 3-D Secure, empreinte d'appareil, *velocity rules*. C'est la couche que les outils de test tentent de contourner — et c'est précisément celle qui les détecte.

---

## 2. 3-D SECURE ET LA NOTION DE "NO VBV"

**VBV** (*Verified by Visa*, aujourd'hui 3-D Secure 1) et **3DS2** ajoutent une authentification du porteur : mot de passe, code SMS, ou biométrie dans l'application bancaire.

Un émetteur décide, **carte par carte**, s'il impose 3DS :

| Configuration | Conséquence |
|---|---|
| 3DS **obligatoire** | Sans le code, l'autorisation échoue. |
| 3DS **supporté, non imposé** | Le marchand choisit de forcer ou non l'authentification. Zone grise. |
| **Pas de 3DS** | Autorisation possible avec numéro + date + CVV seuls. |

L'expression "no VBV" désigne donc une carte dont l'émetteur n'exige pas 3DS **et** pour laquelle le marchand ne force pas l'authentification. Cela dépend autant du marchand que de la carte.

Depuis 2021, cette catégorie s'est effondrée :

- **PSD2** en Europe impose l'authentification forte (SCA) pour la plupart des
paiements en ligne ;
- **Visa / Mastercard** ont rendu 3DS2 obligatoire pour les marchands de l'EEE ;
- des **exemptions** existent (faible montant, *Transaction Risk Analysis*),
mais elles reposent sur le profil de risque du marchand, pas sur la carte.

Résultat : les cartes "no 3DS" exploitables de façon générique sont devenues rares, et celles qui le restent sont les premières monitorées.

---

## 3. AVS ET CVV — LES DEUX AUTRES BARRIÈRES

### AVS (Address Verification System)

Le marchand compare l'adresse déclarée (numéro de rue + code postal) avec celle enregistrée par la banque. Réponses possibles :

- correspondance complète ;
- correspondance partielle (rue OK / code postal non, ou l'inverse) ;
- aucune correspondance ;
- indisponible.

Très utilisé aux **États-Unis, Royaume-Uni, Canada**. Peu répandu en Europe continentale.

Un test AVS n'apprend qu'une chose : si les données d'adresse collent. Il ne donne aucun accès à l'argent.

### CVV / CVC2

Les 3 chiffres au dos de la carte. Ils ne peuvent **pas** être stockés par le marchand (interdiction PCI-DSS), donc ils ne servent qu'une fois et ne "vérifient" rien d'autre que la possession physique de la carte. Un test CVV ne donne aucune information réutilisable.

---

## 4. COMMENT LES PASSERELLES DÉTECTENT UN OUTIL DE TEST

C'est la partie utile — de l'ingénierie de détection réelle.

### Côté marchand / PSP (prestataire de paiement)

- **Velocity rules** — N tentatives par carte, par IP, par BIN, par appareil,
par minute. Un outil qui teste 50 cartes en 30 secondes déclenche le flag immédiatement.
- **Détection de BIN attack** — beaucoup de cartes du même BIN testées avec de
petits montants (0,00 $, 1,00 $) est une signature classique. Stripe Radar, Adyen ou Checkout.com ont des modèles dédiés.
- **Empreinte d'appareil** — canvas, WebGL, polices installées, fuseau horaire,
résolution, en-têtes TLS (JA3/JA4), ordre des extensions. Un navigateur automatisé a une empreinte reconnaissable même avec un *user-agent* falsifié.
- **Réputation IP / ASN** — datacenter, proxy résidentiel réutilisé, nœuds de
sortie Tor → score de risque élevé.
- **Comportement** — absence de souris, pas de scroll, navigation directe vers
le paiement, remplissage anormalement rapide des formulaires.
- **E-mail / téléphone jetables** — domaines déjà blacklistés.

### Côté réseau (Visa / Mastercard)

- **VAMP** (*Visa Acquirer Monitoring Program*) et programmes équivalents
Mastercard — le ratio fraude / chargeback est surveillé **par acquéreur**. Un marchand qui dépasse le seuil perd son compte.
- **BIN pièges / honeypots** — des plages de cartes surveillées spécialement,
invalidées en temps réel. Un outil qui les touche est marqué, et ses IP / appareils sont diffusés.
- **Partage inter-émetteurs** — une carte testée sur dix sites en une heure
remonte comme suspecte chez la banque, qui la bloque.
- **Données 3DS2** — même quand 3DS est "exempté", l'empreinte d'appareil 3DS2
tourne en arrière-plan et remonte des signaux au réseau.

---

## 5. CONCLUSION TECHNIQUE

Un "finder no VBV" ne trouve pas des cartes *utilisables* — il trie des cartes *non encore bloquées*. La fenêtre d'exploitation est courte pour des raisons structurelles :

1. la banque bloque après deux ou trois tentatives échouées ;
2. le réseau diffuse les BIN et les IP après quelques heures ;
3. le marchand perd son compte acquéreur après un pic de tests ;
4. les passerelles partagent leurs listes de blocklist.

D'où la durée de vie de ces outils : quelques jours à quelques semaines avant d'être blacklistés partout — et leurs opérateurs avec eux. Les programmes VAMP / chargeback sont précisément conçus pour cela.

---

## 6. CADRE LÉGAL (RAPPEL FACTUEL)

- **France** : accès ou maintien frauduleux dans un système de traitement
automatisé de données (art. 323-1 du Code pénal), escroquerie (art. 313-1), faux et usage de faux, recel. Peines cumulables.
- **UE** : directive 2019/713 sur la fraude et la contrefaçon des moyens de
paiement.
- **US** : 18 U.S.C. § 1029 (fraud and related activity in connection with
access devices).

La détention ou l'usage d'un outil conçu pour tester des moyens de paiement volés est en soi une infraction dans la plupart des juridictions.

---

## 7. PISTES DE RECHERCHE LÉGITIMES

- **Bug bounty** sur les passerelles de paiement (Stripe, Adyen, Checkout.com
ont des programmes).
- **Étude des modèles de détection** : publications sur la détection de BIN
attacks, la fraude par carte, le *device fingerprinting*.
- **3DS2 et SCA** : documentation technique EMVCo, spécifications de
l'EBA (Autorité bancaire européenne).
- **Sécurité des protocoles de paiement** : MT700/SWIFT, ISO 8583, tokenisation
réseau (Visa Token Service).
