# fraud-repo

Recueil de notes d'analyse sur la mécanique de la fraude financière, des
instruments de paiement et des intrusions bancaires.

Les deux grands manuels existent en version anglaise et française, en deux
formats : `.txt` (mise en page fixe, 79 colonnes) et `.md` (édition Markdown
générée depuis le `.txt` avec un sommaire cliquable). Les notes plus courtes
sont bilingues également, mais en `.md` uniquement.

## Documents

| Sujet | Anglais | Français |
|---|---|---|
| Économie de la fraude — anatomie, mécanique, maximisation | [`the-economics-of-fraud.md`](the-economics-of-fraud.md) · [`.txt`](the-economics-of-fraud.txt) | [`manuel-economie-fraude.md`](manuel-economie-fraude.md) · [`.txt`](manuel-economie-fraude.txt) |
| Rétro-ingénierie du protocole MT700 (crédit documentaire SWIFT) | [`mt700-reverse-engineering.md`](mt700-reverse-engineering.md) · [`.txt`](mt700-reverse-engineering.txt) | [`mt700-reverse-engineering-fr.md`](mt700-reverse-engineering-fr.md) · [`.txt`](mt700-reverse-engineering-fr.txt) |
| Mécanique de vérification des cartes — 3DS, AVS, détection | [`card-verification-mechanics.md`](card-verification-mechanics.md) | [`mechanique-verification-cartes-fr.md`](mechanique-verification-cartes-fr.md) |
| Compromission d'une banque — accès, résidence, mouvement de fonds | [`bank-intrusion-tradecraft.md`](bank-intrusion-tradecraft.md) | [`bank-intrusion-tradecraft-fr.md`](bank-intrusion-tradecraft-fr.md) |

## Outils

| Fichier | Rôle |
|---|---|
| [`tools/txt2md.py`](tools/txt2md.py) | Convertit les manuels `.txt` à mise en page fixe en éditions Markdown avec sommaire cliquable. |
| [`tools/rof.py`](tools/rof.py) | Calculateur interactif de *Return on Fraud* (RoF) et d'analyse de sensibilité — modèle du chapitre 13, annexe E. |

```bash
python3 tools/txt2md.py                       # régénère tous les .md depuis les .txt
python3 tools/txt2md.py the-economics-of-fraud.txt
python3 tools/rof.py                          # interactif, français
python3 tools/rof.py --lang en --example --no-input
```

## Portée

Ces documents décrivent des mécanismes — comment les contrôles fonctionnent,
où ils cassent, comment ils se détectent. Ils sont destinés à la recherche, à
la formation et à la conception de défenses. Aucun ne contient de données
réelles, de coordonnées de comptes ou de matériel exploitable contre un système
en production.
