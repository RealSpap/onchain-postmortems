# On-Chain Postmortems

Reconstructions forensiques indépendantes, faites entièrement on-chain,
d'incidents de sécurité DeFi et plus largement on-chain. Chaque entrée part
d'une source primaire du protocole concerné (ses propres registres de
déploiement GitHub, jamais un article de presse) et reconstruit l'exploit
depuis la donnée brute de la chaîne : `eth_getLogs`, reçus de transaction
décodés, lectures `eth_call` en direct. Quand la presse ou DefiLlama se
trompe sur un chiffre, un périmètre ou une étiquette, ce repo le dit et
montre la preuve on-chain.

Ce repo regroupe 8 postmortems qui vivaient jusqu'ici dans 8 dépôts GitHub
séparés. La fusion se justifie parce qu'un dépôt par incident ne tient pas
à l'échelle : 8 dépôts aujourd'hui et 50 demain donneraient 50 endroits à
fouiller au lieu d'un seul. Chaque incident garde son propre sous-dossier
avec son script, son registre d'hypothèses et ses fichiers de preuves
bruts. Rien n'a été résumé ou perdu dans la fusion.

## En un coup d'œil

| | |
|---|---|
| Incidents couverts | 8, du 21 août au 7 septembre 2026, chacun reconstruit indépendamment on-chain |
| Perte cumulée, recalculée | Environ 29,5 M$ sur les 8 incidents (29 517 493 $ exactement, somme des chiffres du tableau ci-dessous). Deux entrées, Sandbox et Balancer V1, sont des planchers connus : leur repo source refuse explicitement d'affirmer un total agrégé en dollars, donc le vrai cumul est plus élevé que 29,5 M$ |
| Corrections apportées à la presse ou à DefiLlama | 4 des 8 incidents publiés à la fusion corrigent au moins un chiffre ou une étiquette déjà publiée : Sandbox (perte réelle environ 5,2 fois le chiffre rapporté), Balancer V1 (4 pools vidés, pas le seul rapporté), Notional V1 (le flux DefiLlama étiquette lui-même le contrat exploité "V2", alors qu'il s'agit de V1), Cozy V2 Optimism (le chiffre de Cozy et celui de DefiLlama sous-évaluent tous les deux le total vérifié on-chain). Ce compte est mis à jour à la main à chaque nouvelle correction trouvée, `add_new_entry.py` ne le touche pas |
| Méthode | Chaque sous-dossier garde son script Python de reconstruction original, son registre de falsification `registre_hypotheses.csv` et la sortie brute de son script dans `resultats_*.txt`, donc chaque chiffre ci-dessous peut être vérifié contre le fichier qui l'a produit |
| Licence | MIT sur les 8 entrées, un seul auteur (s_pap, 2026) |

## Index

Trié par perte recalculée, décroissant. La colonne "Type/Mécanisme" reflète
ce que la reconstruction on-chain a réellement trouvé, pas l'étiquette de
presse de l'incident.

| Protocole | Date | Perte ($) | Chaîne | Type/Mécanisme | Lien |
|---|---|---|---|---|---|
| Moonwell (marché MAMO) | 2026-08-27 | ≈ 9 131 000 [^moonwell] | Base | Donation attack sur le taux de change d'un marché illiquide, combinée à une manipulation de collatéral/oracle | [moonwell-mamo-oracle/](moonwell-mamo-oracle/) |
| Term Finance (Meta Vault) | 2026-08-17 / 08-23 | ≈ 8 500 000 [^termfinance] | Ethereum | Gouvernance détournée : proposition auto-votée par un wallet neuf sur un exécuteur déployé par l'attaquant, délai normal de 6 jours écoulé sans veto | [termfinance-metavault-governance/](termfinance-metavault-governance/) |
| Tectonic | 2026-08-30 | ≈ 8 300 000 [^tectonic] | Cronos | Donation attack (mint récursif de collatéral puis dons directs au contrat de marché) gonflant un taux de change, emprunt massif contre le collatéral gonflé, suivi d'un rollback de chaîne | [tectonic-cronos/](tectonic-cronos/) |
| Notional Finance (V1 Escrow) | 2026-09-03 / 09-04 | 1 727 782 [^notional] | Ethereum | Overflow/downcast `uint128` dans la valorisation du collatéral du contrat Escrow legacy V1 | [notional-v1-escrow/](notional-v1-escrow/) |
| Ajna Finance | 2026-08-28 / 08-29 | ≈ 775 400 [^ajna] | Ethereum | Exploit de la math de liquidation (`Kick`) sur des pools déployés via une factory non documentée par le protocole | [ajna-liquidation/](ajna-liquidation/) |
| The Sandbox (SAND / OFT) | 2026-08-21 / 08-22 | ≥ 675 000 [^sandbox] | Base + BSC + Ethereum | Hijack du delegate LayerZero via une primitive `approveAndCall` héritée, un bug de composition, pas une clé compromise | [sandbox-oft-delegate-hijack/](sandbox-oft-delegate-hijack/) |
| Balancer V1 (pools legacy) | 2026-08-30 / 08-31 | ≥ 234 000 [^balancer] | Ethereum | Erreur d'arrondi sur des pools V1 non maintenus, join répété à 1 satoshi | [balancer-v1-rounding/](balancer-v1-rounding/) |
| Cozy V2 | 2026-09-02 / 09-07 | 174 311 [^cozy] | Optimism | Réponses fausses non contestées à l'UMA Optimistic Oracle pendant sa fenêtre de contestation de 5 jours | [cozy-v2-optimism/](cozy-v2-optimism/) |

[^moonwell]: Dette encore non recouvrée au 28 août 2026 selon le postmortem officiel de Moonwell (595 liquidations sur 11,03 M$ empruntés bruts, 9,131 M$ restaient non couverts à cette date). La presse (PeckShield/CertiK) a diffusé environ 8,7 M$. Voir `moonwell-mamo-oracle/README.md`.
[^termfinance]: Chiffre de presse, cohérent avec les montants vérifiés indépendamment on-chain (2 841,7435 WETH drainés du Meta Vault ETH, plus 1 679 639,290442 USDC balayés puis reconvertis en 1 679 642,454089 DAI). Aucun total en dollars n'a été recalculé indépendamment dans le repo source. Voir `termfinance-metavault-governance/README.md`.
[^tectonic]: Perte confirmée irrécupérable après le rollback d'environ 11 000 blocs par les validateurs Cronos. Plus de 120 M$ avaient été empruntés contre le collatéral gonflé, mais la majorité de cette dette a été effacée par le rollback lui-même. Voir `tectonic-cronos/README.md` et le tableau de bord Dune qui y est lié.
[^notional]: 69 257,3727 DAI plus 1 658 524,8641 USDC, décodés directement depuis les événements `Transfer` de la transaction d'extraction, soit 1 727 782,2368 $. Ce montant correspond exactement au champ `amount` du flux public DefiLlama pour cet incident, qui étiquette pourtant l'incident "Notional V2" alors que le contrat exploité est V1. Voir `notional-v1-escrow/README.md`.
[^ajna]: Chiffre de presse et DefiLlama pour l'ensemble des 7 pools touchés. Une seule extraction est confirmée transaction par transaction (49,32 WETH sur le pool cbETH/WETH, environ 121 800 $ à 2 470 $/ETH). Le reste repose sur un delta de solde avant/après, une preuve plus faible, et le projet source ne force pas ce chiffre à concorder avec celui de la presse. Voir `ajna-liquidation/README.md`.
[^sandbox]: Chiffre de presse, jambe Ethereum uniquement. La reconstruction indépendante trouve un montant réel environ 5,2 fois plus élevé (405,828879423128923336 WETH bruts sur les 2 chaînes réellement vidées, Base et Ethereum), mais le repo source affirme explicitement n'assigner aucun total en dollars à ce chiffre natif. Voir `sandbox-oft-delegate-hijack/README.md`.
[^balancer]: Chiffre DefiLlama et presse pour 1 seul pool. La reconstruction indépendante trouve que le même portefeuille a vidé 4 pools distincts la même nuit. Les 3 pools additionnels ne sont chiffrés qu'en nature (DAI, USDC, MKR, UMA, LINK, SNX, AMPL, WBTC, BLZ, WSTA et autres) : le repo source n'agrège aucun total en dollars, faute de flux de prix historique fiable pour ces tokens. Voir `balancer-v1-rounding/README.md`.
[^cozy]: 174 311,006968 USDC.e, vérifié par deux méthodes indépendantes qui tombent sur le même total (somme des transferts de chaque transaction de réclamation, puis filtre de logs indépendant sur l'adresse de destination). Ce chiffre dépasse à la fois celui publié par Cozy elle-même (170 186 $) et celui suivi par DefiLlama (163 326 $, qui correspond exactement à une seule des deux transactions de réclamation). Voir `cozy-v2-optimism/README.md`.

## Structure

```
onchain-postmortems/
  README.md                          ce fichier
  add_new_entry.py                   scaffold un nouveau sous-dossier et met a jour l'index
  LICENSE                            MIT, s_pap 2026
  <slug-incident>/
    README.md                        recit complet, "at a glance", methode, caveats
    reconstruct_exploit.py           script qui interroge la chaine en direct
    registre_hypotheses.csv          chaque hypothese avec son test de falsification et son niveau de preuve
    resultats_*.txt                  sortie brute, non editee, du script
    LICENSE, .gitignore              conserves tels quels depuis le repo d'origine
```

Chacun des 8 sous-dossiers ci-dessus était, jusqu'au regroupement dans ce
repo, son propre dépôt GitHub public sous le compte `RealSpap`. Ces 8 dépôts
restent visibles et publics, ils ne sont pas supprimés, mais leur contenu
canonique vit désormais ici et leur README pointe vers ce repo.

| Ancien dépôt | Sous-dossier ici |
|---|---|
| `RealSpap/sandbox-oft-delegate-hijack-exploit-postmortem` | `sandbox-oft-delegate-hijack/` |
| `RealSpap/moonwell-mamo-oracle-exploit-postmortem` | `moonwell-mamo-oracle/` |
| `RealSpap/balancer-v1-legacy-pools-rounding-exploit-postmortem` | `balancer-v1-rounding/` |
| `RealSpap/termfinance-metavault-governance-exploit-postmortem` | `termfinance-metavault-governance/` |
| `RealSpap/notional-v1-escrow-exploit-postmortem` | `notional-v1-escrow/` |
| `RealSpap/ajna-liquidation-exploit-postmortem` | `ajna-liquidation/` |
| `RealSpap/cozy-v2-optimism-postmortem` | `cozy-v2-optimism/` |
| `RealSpap/tectonic-cronos-postmortem` | `tectonic-cronos/` |

## Ajouter un nouvel incident

```bash
python3 add_new_entry.py \
  --slug new-protocol-incident \
  --name "New Protocol" \
  --date 2026-10-01 \
  --loss-usd 1234567 \
  --chain "Ethereum" \
  --mechanism "Reentrancy dans le chemin de retrait" \
  --readme-url "https://example.com/postmortem"
```

Ceci scaffold `new-protocol-incident/` avec un README stub, un
`registre_hypotheses.csv` vide et un `reconstruct_exploit.py` stub, puis
insère une nouvelle ligne dans le tableau d'index ci-dessus, triée par
perte, et recalcule la ligne du nombre d'incidents et de la perte cumulée
dans le bloc "en un coup d'œil" à partir du tableau lui-même, jamais depuis
un nombre codé en dur. Voir `add_new_entry.py --help` pour la liste
complète des options, et utiliser `--loss-known-partial` pour un incident
comme Sandbox ou Balancer V1 ci-dessus, où la perte réelle est connue pour
dépasser le chiffre qu'on peut effectivement sourcer.

Le script ne touche pas aux lignes "Corrections apportées" et "Licence" du
bloc "en un coup d'œil", ce sont des jugements humains (est-ce que ce
nouvel incident corrige vraiment la presse, est-ce vraiment du MIT), pas
des totaux mécaniques. Mets-les à jour toi-même si besoin.

## Périmètre

Ce programme couvre des incidents DeFi aujourd'hui, mais le nom est
délibérément `onchain-postmortems`, pas `defi-postmortems` : une future
entrée n'a pas besoin d'être un protocole de prêt ou d'AMM. Un hack de
bridge, un incident d'infrastructure L1/L2, ou une compromission de set de
validateurs a tout autant sa place ici, du moment qu'il reçoit le même
traitement : une reconstruction on-chain indépendante depuis une source
primaire, pas un résumé de la couverture de presse.

## Limites

- Ceci est une recherche indépendante, pas un audit de sécurité, et n'est
  affilié à aucun protocole, auditeur ou média cité dans un sous-dossier.
- Chaque chiffre en dollars du tableau d'index ci-dessus est recalculé
  depuis les fichiers sources de chaque sous-dossier (son README, la
  sortie brute de son script dans `resultats_*.txt`, ou son
  `registre_hypotheses.csv`), jamais recopié d'un ancien résumé sans le
  vérifier contre ces fichiers. Quand la donnée source d'un sous-dossier
  ne permet pas un total en dollars complet, le tableau le dit en note de
  bas de page plutôt que d'en inventer un.
- Deux entrées (Sandbox, Balancer V1) rapportent un chiffre en dollars qui
  est un plancher connu, pas un total complet, parce que leur repo source
  a trouvé un périmètre plus large que la presse sans convertir chaque
  montant récupéré en dollars. Lire le sous-dossier lié pour la
  comptabilité complète en unités natives.
- Les entrées Tectonic et Moonwell rapportent le chiffre confirmé
  irrécupérable ou encore non recouvré, pas le montant brut, plus élevé,
  emprunté ou extrait avant que des liquidations et, pour Tectonic, un
  rollback de chaîne n'en récupèrent une partie. Les deux lectures sont
  données en note de bas de page et dans le sous-dossier lié.
- `tectonic-cronos/` est le seul sous-dossier sans `resultats_*.txt` ni
  `registre_hypotheses.csv` : son script est un outil de lecture de l'état
  actuel de la chaîne (`tectonic_risk_snapshot.py`), pas un rejeu de
  l'incident, et ses chiffres de perte (120 M$+ empruntés, 8,3 M$
  irrécupérables) reposent sur son README et sur le tableau de bord Dune
  qu'il lie, pas sur un fichier de sortie reproductible localement dans ce
  repo. Signalé ici plutôt que masqué.

## Licence

MIT. Voir `LICENSE`.
