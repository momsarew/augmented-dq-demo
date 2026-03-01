"""
Référentiel complet des anomalies pour les 4 dimensions de risque DQ.

Source unique de vérité : backend/rules_catalog.yaml
Ce module expose les mêmes APIs qu'avant (REFERENTIAL, get_by_dimension,
get_summary, etc.) mais charge les données depuis le catalogue YAML
déclaratif pour faciliter l'extension.

Pour ajouter de nouvelles anomalies → éditer rules_catalog.yaml
"""

from backend.rules_catalog_loader import catalog as _catalog


# ============================================================================
# DB — Database Integrity (22 anomalies)
# ============================================================================

# DB#1: NULL non autorisés [CRITIQUE] [Auto] [SAST]
# DB#2: Violations clé primaire [CRITIQUE] [Auto] [SAMT]
# DB#3: Violations clé étrangère [CRITIQUE] [Auto] [MR]
# DB#4: Violations contraintes unicité [ÉLEVÉ] [Auto] [SAMT]
# DB#5: Valeurs hors domaine [ÉLEVÉ] [Auto] [SAST]
# DB#6: Valeurs hors plage numérique [ÉLEVÉ] [Auto] [SAST]
# DB#7: Violations de format [MOYEN] [Auto] [SAST]
# DB#8: Erreurs de type données [ÉLEVÉ] [Auto] [SAST]
# DB#9: Doublons exacts [ÉLEVÉ] [Auto] [SAMT]
# DB#10: Doublons proches (fuzzy) [MOYEN] [Semi] [SAMT, SR, MR, MDS]
# DB#11: Redondance inter-tables [MOYEN] [Semi] [MR]
# DB#12: Synonymes [MOYEN] [Semi] [SAMT, MR, MDS]
# DB#13: Homonymes [CRITIQUE] [Manuel] [MAST, MR, MDS]
# DB#14: Hétérogénéité unités [CRITIQUE] [Semi] [SAMT, MR, MDS]
# DB#15: Incohérences format colonnes [FAIBLE] [Auto] [MAST]
# DB#16: Données manquantes (NULL légitimes) [VARIABLE] [Auto] [SAST]
# DB#17: Lignes manquantes [ÉLEVÉ] [Manuel] [SR, MR]
# DB#18: Colonnes entières vides [FAIBLE] [Auto] [SAMT]
# DB#19: Problèmes encodage [MOYEN] [Auto] [SAST]
# DB#20: Caractères spéciaux non échappés [MOYEN] [Auto] [SAST]
# DB#21: Espaces parasites [MOYEN] [Auto] [SAST]
# DB#22: Casse incohérente [FAIBLE] [Auto] [SAMT]

# ============================================================================
# DP — Data Processing (32 anomalies)
# ============================================================================

# DP#1: Calculs dérivés incorrects [ÉLEVÉ] [Semi] [MAST]
# DP#2: Erreurs d'arrondi [MOYEN] [Semi] [MAST, SAMT]
# DP#3: Débordements numériques [CRITIQUE] [Auto] [SAMT]
# DP#4: Divisions par zéro [MOYEN] [Auto] [SAST, MAST]
# DP#5: Erreurs d'agrégations [ÉLEVÉ] [Semi] [SAMT, SR]
# DP#6: Conversions type inappropriées [ÉLEVÉ] [Semi] [SAST, SAMT]
# DP#7: Troncatures de données [MOYEN] [Auto] [SAST]
# DP#8: Conversions format dates [CRITIQUE] [Semi] [SAST, MDS]
# DP#9: Problèmes de transcodage [CRITIQUE] [Semi] [MR, MDS]
# DP#10: Conversions unités mesure [CRITIQUE] [Semi] [SAST, SAMT, MDS]
# DP#11: Pertes lignes INNER JOIN [CRITIQUE] [Semi] [MR]
# DP#12: Duplications jointures 1-N [CRITIQUE] [Semi] [MR]
# DP#13: Clés jointure incorrectes [CRITIQUE] [Manuel] [MR]
# DP#14: Jointures cartésiennes [CRITIQUE] [Auto] [MR]
# DP#15: Fusion IDs conflictuels [CRITIQUE] [Semi] [MDS]
# DP#16: Conditions WHERE incorrectes [MOYEN] [Manuel] [SAMT, SR]
# DP#17: Fenêtres temporelles incorrectes [MOYEN] [Manuel] [SAMT, SR]
# DP#18: DISTINCT mal placé [MOYEN] [Semi] [SAMT]
# DP#19: Erreurs GROUP BY [ÉLEVÉ] [Semi] [SAMT, SR]
# DP#20: Données non chargées [CRITIQUE] [Semi] [SR, MR, MDS]
# DP#21: Ordre exécution incorrect [MOYEN] [Manuel] [SR]
# DP#22: Transformations non idempotentes [ÉLEVÉ] [Manuel] [SR]
# DP#23: Données obsolètes cache [MOYEN] [Semi] [MR, MDS]
# DP#24: Échecs de propagation [ÉLEVÉ] [Semi] [MR, MDS]
# DP#25: Agrégations mauvaise granularité [MOYEN] [Manuel] [SAMT, SR]
# DP#26: Valeurs pré-calculées obsolètes [MOYEN] [Semi] [MAST, SR]
# DP#27: Perte de granularité [MOYEN] [Manuel] [SAMT, SR]
# DP#28: Fenêtres temps incorrectes agrégations [MOYEN] [Semi] [SAMT, SR]
# DP#29: Règles déduplication trop agressives [ÉLEVÉ] [Manuel] [SAMT, SR, MR]
# DP#30: Règles déduplication trop laxistes [MOYEN] [Manuel] [SAMT, SR, MR]
# DP#31: Choix master record incorrect [ÉLEVÉ] [Manuel] [SAMT, SR, MR]
# DP#32: Perte historique déduplication [MOYEN] [Manuel] [SR, MR]

# ============================================================================
# BR — Business Rules (34 anomalies)
# ============================================================================

# BR#1: Incohérences temporelles [ÉLEVÉ] [Auto] [MAST]
# BR#2: Valeurs hors bornes métier [CRITIQUE] [Auto] [MAST]
# BR#3: Combinaisons interdites [ÉLEVÉ] [Semi] [MAST]
# BR#4: Cardinalités métier violées [MOYEN] [Semi] [MR]
# BR#5: Obligations métier non respectées [ÉLEVÉ] [Semi] [MAST]
# BR#6: Non-conformité protection données [CRITIQUE] [Manuel] [MR, MDS]
# BR#7: Non-conformité légale sectorielle [CRITIQUE] [Manuel] [MR, MDS]
# BR#8: Non-conformité fiscale/comptable [CRITIQUE] [Manuel] [MR]
# BR#9: Non-conformité standards métier [MOYEN] [Manuel] [MR]
# BR#10: Exigences audit non satisfaites [ÉLEVÉ] [Semi] [SR, MR]
# BR#11: Incohérences calculés vs base [ÉLEVÉ] [Auto] [MAST]
# BR#12: Sommes de contrôle incorrectes [CRITIQUE] [Auto] [SAMT, SR]
# BR#13: Ratios métier invalides [MOYEN] [Auto] [MAST]
# BR#14: Dépendances fonctionnelles violées [ÉLEVÉ] [Semi] [MAST, SR]
# BR#15: Exclusivité mutuelle violée [ÉLEVÉ] [Auto] [MAST]
# BR#16: Hiérarchies incohérentes [ÉLEVÉ] [Semi] [SR]
# BR#17: Classifications métier incorrectes [MOYEN] [Manuel] [MAST, MR]
# BR#18: Niveau hiérarchique incohérent [MOYEN] [Semi] [MAST, SR]
# BR#19: Appartenance multiple interdite [MOYEN] [Auto] [MAST]
# BR#20: Changements niveau illogiques [FAIBLE] [Manuel] [SR]
# BR#21: Politiques internes non respectées [MOYEN] [Manuel] [MAST, MR]
# BR#22: Seuils budgétaires dépassés [ÉLEVÉ] [Semi] [MAST, SR]
# BR#23: Processus approbation contournés [ÉLEVÉ] [Manuel] [SR, MR]
# BR#24: Règles éligibilité non vérifiées [MOYEN] [Semi] [MAST, MR]
# BR#25: Politiques sécurité violées [CRITIQUE] [Manuel] [MR, MDS]
# BR#26: Événements dans mauvais ordre [ÉLEVÉ] [Semi] [SR]
# BR#27: Délais réglementaires dépassés [CRITIQUE] [Semi] [MAST, SR]
# BR#28: Périodes validité incohérentes [MOYEN] [Semi] [SR]
# BR#29: Fréquence événements anormale [MOYEN] [Semi] [SR]
# BR#30: Antériorité requise non respectée [MOYEN] [Semi] [SR, MR]
# BR#31: Dossiers incomplets [ÉLEVÉ] [Manuel] [MR]
# BR#32: Validations métier absentes [ÉLEVÉ] [Manuel] [MR]
# BR#33: Documents justificatifs manquants [MOYEN] [Manuel] [MR]
# BR#34: Approbations manquantes [ÉLEVÉ] [Manuel] [MR]

# ============================================================================
# UP — Usage Appropriateness (40 anomalies)
# ============================================================================

# UP#1: Granularité trop fine [FAIBLE] [Manuel] [MAST]
# UP#2: Granularité trop large [MOYEN] [Manuel] [MAST]
# UP#3: Niveau agrégation incorrect [MOYEN] [Manuel] [SAMT, SR]
# UP#4: Résolution temporelle inadaptée [MOYEN] [Manuel] [SAMT, SR]
# UP#5: Résolution spatiale inadéquate [MOYEN] [Manuel] [SAMT]
# UP#6: Données obsolètes [ÉLEVÉ] [Semi] [SAMT]
# UP#7: Latence excessive [ÉLEVÉ] [Semi] [SR, MDS]
# UP#8: Fréquence MAJ insuffisante [MOYEN] [Semi] [SAMT, SR]
# UP#9: Données futures inappropriées [MOYEN] [Manuel] [MAST]
# UP#10: Version donnée incorrecte [MOYEN] [Manuel] [SAMT]
# UP#11: Précision insuffisante [MOYEN] [Manuel] [MAST]
# UP#12: Précision excessive [FAIBLE] [Manuel] [MAST]
# UP#13: Marge erreur trop élevée [ÉLEVÉ] [Manuel] [MAST]
# UP#14: Niveau confiance insuffisant [CRITIQUE] [Manuel] [SAMT, SR]
# UP#15: Source non fiable pour usage [ÉLEVÉ] [Manuel] [MR, MDS]
# UP#16: Taux remplissage insuffisant [ÉLEVÉ] [Semi] [SAMT]
# UP#17: Attributs manquants pour usage [ÉLEVÉ] [Semi] [MAST, MR]
# UP#18: Périmètre incomplet [MOYEN] [Manuel] [SR, MR]
# UP#19: Historique insuffisant [MOYEN] [Manuel] [SR]
# UP#20: Couverture géographique partielle [MOYEN] [Manuel] [SAMT]
# UP#21: Format inexploitable [MOYEN] [Manuel] [MDS]
# UP#22: Granularité accès inadéquate [MOYEN] [Manuel] [SR, MR]
# UP#23: Données non interprétables [ÉLEVÉ] [Manuel] [MR]
# UP#24: Langue inappropriée [FAIBLE] [Manuel] [SAMT]
# UP#25: Encodage incompatible [MOYEN] [Semi] [MDS]
# UP#26: Périmètre trop large [FAIBLE] [Manuel] [SR, MR]
# UP#27: Périmètre trop restreint [MOYEN] [Manuel] [SR, MR]
# UP#28: Population cible incorrecte [MOYEN] [Manuel] [SR]
# UP#29: Période temporelle inadaptée [MOYEN] [Manuel] [SR]
# UP#30: Dimensions analytiques manquantes [MOYEN] [Manuel] [MR]
# UP#31: Définition ambiguë [MOYEN] [Manuel] [MAST]
# UP#32: Unités non précisées [MOYEN] [Manuel] [MAST]
# UP#33: Référentiel inadapté [FAIBLE] [Manuel] [MR]
# UP#34: Contexte métier manquant [MOYEN] [Manuel] [MR]
# UP#35: Méthode calcul non documentée [MOYEN] [Manuel] [MAST, SR]
# UP#36: Données non conformes usage légal [CRITIQUE] [Manuel] [MR, MDS]
# UP#37: Habilitation insuffisante [CRITIQUE] [Manuel] [MR]
# UP#38: Traçabilité inadéquate [ÉLEVÉ] [Manuel] [SR, MR]
# UP#39: Durée conservation dépassée [MOYEN] [Semi] [SAMT]
# UP#40: Finalité usage non autorisée [CRITIQUE] [Manuel] [MDS]


# ============================================================================
# REFERENTIAL chargé depuis rules_catalog.yaml (source unique de vérité)
# ============================================================================
REFERENTIAL = _catalog.referential


# ============================================================================
# Ancien dictionnaire hardcodé conservé en commentaire de référence.
# Toutes les anomalies sont maintenant dans backend/rules_catalog.yaml
# ============================================================================

_LEGACY_REFERENTIAL_REMOVED = {
    "DB#1": {
        "name": "NULL non autorisés",
        "description": "Attributs obligatoires (1,1) contenant NULL",
        "dimension": "DB",
        "academic_dims": "Completeness, Validity",
        "detection": "Auto",
        "criticality": "CRITIQUE",
        "woodall": "SAST",
        "algorithm": "Domain analysis: WHERE col IS NULL",
        "complexity": "O(1)",
        "business_risk": "Le risque métier est le blocage de la paie ou de la facturation, car une information obligatoire manquante empêche le système d’identifier correctement l’employé ou le client à traiter",
    },
    "DB#2": {
        "name": "Violations clé primaire",
        "description": "Doublons sur contrainte PK",
        "dimension": "DB",
        "academic_dims": "Redundancy, Correctness",
        "detection": "Auto",
        "criticality": "CRITIQUE",
        "woodall": "SAMT",
        "algorithm": "Column analysis: GROUP BY pk HAVING COUNT(*)>1",
        "complexity": "O(n)",
        "business_risk": "Le risque métier est de compter ou payer plusieurs fois la même personne, car la présence de doublons empêche de distinguer une entité unique",
    },
    "DB#3": {
        "name": "Violations clé étrangère",
        "description": "Références vers entités inexistantes (orphelins)",
        "dimension": "DB",
        "academic_dims": "Consistency, Correctness",
        "detection": "Auto",
        "criticality": "CRITIQUE",
        "woodall": "MR",
        "algorithm": "PK/FK analysis: LEFT JOIN + WHERE IS NULL",
        "complexity": "O(n+m)",
        "business_risk": "Le risque métier est l’impossibilité de relier certaines données à un employé, un client ou un produit, car la référence associée n’existe pas",
    },
    "DB#4": {
        "name": "Violations contraintes unicité",
        "description": "Doublons sur colonnes UNIQUE hors PK",
        "dimension": "DB",
        "academic_dims": "Redundancy, Consistency",
        "detection": "Auto",
        "criticality": "ÉLEVÉ",
        "woodall": "SAMT",
        "algorithm": "Column analysis: GROUP BY col HAVING COUNT(*)>1",
        "complexity": "O(n)",
        "business_risk": "Le risque métier est la confusion entre plusieurs enregistrements représentant la même personne, ce qui fausse le suivi et les décisions",
    },
    "DB#5": {
        "name": "Valeurs hors domaine",
        "description": "Valeur ∉ ensemble prédéfini",
        "dimension": "DB",
        "academic_dims": "Validity, Correctness",
        "detection": "Auto",
        "criticality": "ÉLEVÉ",
        "woodall": "SAST",
        "algorithm": "Domain analysis: WHERE col NOT IN (domain)",
        "complexity": "O(1)",
        "business_risk": "Le risque métier est de mal interpréter une situation (statut, catégorie, type), car la valeur utilisée n’est pas reconnue par le système ou les utilisateurs",
    },
    "DB#6": {
        "name": "Valeurs hors plage numérique",
        "description": "Nombres violant bornes MIN/MAX",
        "dimension": "DB",
        "academic_dims": "Validity, Accuracy",
        "detection": "Auto",
        "criticality": "ÉLEVÉ",
        "woodall": "SAST",
        "algorithm": "Domain analysis: WHERE col<MIN OR col>MAX",
        "complexity": "O(1)",
        "business_risk": "Le risque métier est de produire des montants ou indicateurs faux, car les valeurs saisies dépassent les limites réalistes attendues",
    },
    "DB#7": {
        "name": "Violations de format",
        "description": "Pattern syntaxique incorrect",
        "dimension": "DB",
        "academic_dims": "Validity, Consistency",
        "detection": "Auto",
        "criticality": "MOYEN",
        "woodall": "SAST",
        "algorithm": "Lexical analysis: Regex match",
        "complexity": "O(1)",
        "business_risk": "Le risque métier est le blocage d’un traitement (facture, paie, envoi de document), car l’information n'est pas écrite au bon format",
    },
    "DB#8": {
        "name": "Erreurs de type données",
        "description": "Type physique ≠ type logique",
        "dimension": "DB",
        "academic_dims": "Validity, Correctness",
        "detection": "Auto",
        "criticality": "ÉLEVÉ",
        "woodall": "SAST",
        "algorithm": "Column analysis: Type inference + validation",
        "complexity": "O(1)",
        "business_risk": "Le risque métier est d’obtenir des résultats incorrects, car le système traite une information comme un texte alors qu’elle devrait être un nombre ou une date",
    },
    "DB#9": {
        "name": "Doublons exacts",
        "description": "n tuples identiques (sauf clé)",
        "dimension": "DB",
        "academic_dims": "Redundancy",
        "detection": "Auto",
        "criticality": "ÉLEVÉ",
        "woodall": "SAMT",
        "algorithm": "Column analysis: GROUP BY all_cols HAVING COUNT(*)>1",
        "complexity": "O(n)",
        "business_risk": "Le risque métier est d’avoir des chiffres trop élevés, car une même personne ou opération est comptée plusieurs fois",
    },
    "DB#10": {
        "name": "Doublons proches (fuzzy)",
        "description": "Variations syntaxiques même entité",
        "dimension": "DB",
        "academic_dims": "Redundancy, Consistency",
        "detection": "Semi",
        "criticality": "MOYEN",
        "woodall": "SAMT, SR, MR, MDS",
        "algorithm": "Matching algorithms: Levenshtein, SOUNDEX, NYSIIS, Fellegi-Sunter (1969), Sorted Neighbourhood Method (SNM)",
        "complexity": "O(n²) naïf\n O(n×w) avec SNM\n w=taille fenêtre",
        "business_risk": "Le risque métier est de traiter une même personne comme plusieurs personnes différentes, car de légères variations empêchent de les reconnaître comme identiques",
    },
    "DB#11": {
        "name": "Redondance inter-tables",
        "description": "Même info dans N tables (violation 3NF)",
        "dimension": "DB",
        "academic_dims": "Redundancy, Consistency",
        "detection": "Semi",
        "criticality": "MOYEN",
        "woodall": "MR",
        "algorithm": "Cross-domain analysis: Compare col values across tables",
        "complexity": "O(n×m)",
        "business_risk": "Le risque métier est d’avoir des informations contradictoires, car la même donnée est stockée à plusieurs endroits et mise à jour différemment",
    },
    "DB#12": {
        "name": "Synonymes",
        "description": "N valeurs = même concept",
        "dimension": "DB",
        "academic_dims": "Consistency, Understandability",
        "detection": "Semi",
        "criticality": "MOYEN",
        "woodall": "SAMT, MR, MDS",
        "algorithm": "Column analysis + Dictionary matching",
        "complexity": "O(n×d)\n d=taille dictionnaire",
        "business_risk": "Le risque métier est de produire des analyses incohérentes, car plusieurs termes différents sont utilisés pour désigner la même chose",
    },
    "DB#13": {
        "name": "Homonymes",
        "description": "Même valeur = N concepts selon contexte",
        "dimension": "DB",
        "academic_dims": "Consistency, Interpretability",
        "detection": "Manuel",
        "criticality": "CRITIQUE",
        "woodall": "MAST, MR, MDS",
        "algorithm": "Semantic profiling + Context analysis\n ⚠️ GAP Woodall (pas de méthode auto)",
        "complexity": "Manuel\n (heuristiques)",
        "business_risk": "Le risque métier est de mal interpréter les données, car une même valeur peut avoir des significations différentes selon le contexte",
    },
    "DB#14": {
        "name": "Hétérogénéité unités",
        "description": "Unités différentes même dimension",
        "dimension": "DB",
        "academic_dims": "Consistency, Understandability",
        "detection": "Semi",
        "criticality": "CRITIQUE",
        "woodall": "SAMT, MR, MDS",
        "algorithm": "Column analysis: Detect scale factors (×2.2 kg/lbs, ×1000 k€/€)",
        "complexity": "O(n)",
        "business_risk": "Le risque métier est de faire des calculs faux, car les valeurs comparées n’utilisent pas la même unité de mesure",
    },
    "DB#15": {
        "name": "Incohérences format colonnes",
        "description": "Formats incompatibles attributs liés",
        "dimension": "DB",
        "academic_dims": "Consistency, Readability",
        "detection": "Auto",
        "criticality": "FAIBLE",
        "woodall": "MAST",
        "algorithm": "Format distribution: Analyze date/numeric patterns",
        "complexity": "O(1)",
        "business_risk": "Le risque métier est de ne pas pouvoir croiser les données, car les informations liées ne sont pas stockées sous le même format",
    },
    "DB#16": {
        "name": "Données manquantes (NULL légitimes)",
        "description": "NULL autorisés par modèle (0,1)",
        "dimension": "DB",
        "academic_dims": "Completeness",
        "detection": "Auto",
        "criticality": "VARIABLE",
        "woodall": "SAST",
        "algorithm": "Column analysis: COUNT(col)/COUNT(*) ratio",
        "complexity": "O(1)",
        "business_risk": "Le risque métier est d’avoir une vision incomplète de l’activité, car certaines informations importantes ne sont pas renseignées",
    },
    "DB#17": {
        "name": "Lignes manquantes",
        "description": "Entités absentes de l'univers",
        "dimension": "DB",
        "academic_dims": "Completeness",
        "detection": "Manuel",
        "criticality": "ÉLEVÉ",
        "woodall": "SR, MR",
        "algorithm": "Compare expected vs actual count\n ⚠️ GAP Woodall (nécessite référence externe)",
        "complexity": "O(n) avec référence externe",
        "business_risk": "Le risque métier est de sous-estimer l’activité réelle, car certaines entités attendues sont absentes du système",
    },
    "DB#18": {
        "name": "Colonnes entières vides",
        "description": "Attribut 100% NULL",
        "dimension": "DB",
        "academic_dims": "Completeness",
        "detection": "Auto",
        "criticality": "FAIBLE",
        "woodall": "SAMT",
        "algorithm": "Column analysis: COUNT(col)=0",
        "complexity": "O(n)",
        "business_risk": "Le risque métier est de ne pas exploiter une information prévue, car la donnée n’a jamais été renseignée",
    },
    "DB#19": {
        "name": "Problèmes encodage",
        "description": "Corruption charset (UTF-8, ISO)",
        "dimension": "DB",
        "academic_dims": "Readability, Correctness",
        "detection": "Auto",
        "criticality": "MOYEN",
        "woodall": "SAST",
        "algorithm": "Charset detection: chardet library + validation",
        "complexity": "O(1)",
        "business_risk": "Le risque métier est de mal identifier des personnes, produits ou lieux, car les caractères sont mal interprétés par les systèmes",
    },
    "DB#20": {
        "name": "Caractères spéciaux non échappés",
        "description": "Caractères réservés SQL/XML non traités",
        "dimension": "DB",
        "academic_dims": "Readability, Correctness",
        "detection": "Auto",
        "criticality": "MOYEN",
        "woodall": "SAST",
        "algorithm": "Regex: Search special chars ['\\\"\\\\]",
        "complexity": "O(1)",
        "business_risk": "Le risque métier est que le système ne fonctionne pas correctement, car certains caractères sont mal interprétés",
    },
    "DB#21": {
        "name": "Espaces parasites",
        "description": "Leading/trailing whitespace",
        "dimension": "DB",
        "academic_dims": "Readability, Consistency",
        "detection": "Auto",
        "criticality": "MOYEN",
        "woodall": "SAST",
        "algorithm": "WHERE col <> TRIM(col)",
        "complexity": "O(1)",
        "business_risk": "Le risque métier est que le système ne reconnaisse pas des valeurs pourtant identiques, car des espaces invisibles les rendent différentes",
    },
    "DB#22": {
        "name": "Casse incohérente",
        "description": "Variations majuscules/minuscules",
        "dimension": "DB",
        "academic_dims": "Consistency, Readability",
        "detection": "Auto",
        "criticality": "FAIBLE",
        "woodall": "SAMT",
        "algorithm": "GROUP BY UPPER(col), col; COUNT DISTINCT",
        "complexity": "O(n)",
        "business_risk": "Le risque métier est de créer des doublons ou des erreurs de correspondance, car le système considère des mots identiques comme différents selon les majuscules ou minuscules",
    },
    "DP#1": {
        "name": "Calculs dérivés incorrects",
        "description": "Formule F(A₁,...,Aₙ) non respectée",
        "dimension": "DP",
        "academic_dims": "Correctness, Accuracy",
        "detection": "Semi",
        "criticality": "ÉLEVÉ",
        "woodall": "MAST",
        "algorithm": "Semantic profiling: Verify F(A₁,...,Aₙ) = result",
        "complexity": "O(1)",
    },
    "DP#2": {
        "name": "Erreurs d'arrondi",
        "description": "Perte précision arrondis cumulés",
        "dimension": "DP",
        "academic_dims": "Accuracy",
        "detection": "Semi",
        "criticality": "MOYEN",
        "woodall": "MAST, SAMT",
        "algorithm": "Precision analysis: Compare stored vs recalculated",
        "complexity": "O(n)",
    },
    "DP#3": {
        "name": "Débordements numériques",
        "description": "Overflow/underflow arithmétique",
        "dimension": "DP",
        "academic_dims": "Correctness, Accuracy",
        "detection": "Auto",
        "criticality": "CRITIQUE",
        "woodall": "SAMT",
        "algorithm": "Type analysis: Check value < type_max",
        "complexity": "O(n)",
    },
    "DP#4": {
        "name": "Divisions par zéro",
        "description": "Ratio avec dénominateur=0",
        "dimension": "DP",
        "academic_dims": "Correctness",
        "detection": "Auto",
        "criticality": "MOYEN",
        "woodall": "SAST, MAST",
        "algorithm": "Domain analysis: WHERE denominator = 0",
        "complexity": "O(1)",
    },
    "DP#5": {
        "name": "Erreurs d'agrégations",
        "description": "SUM/AVG/COUNT incorrects",
        "dimension": "DP",
        "academic_dims": "Correctness, Accuracy",
        "detection": "Semi",
        "criticality": "ÉLEVÉ",
        "woodall": "SAMT, SR",
        "algorithm": "Semantic profiling: Validate aggregation logic + NULL handling",
        "complexity": "O(n)",
    },
    "DP#6": {
        "name": "Conversions type inappropriées",
        "description": "Cast perdant information",
        "dimension": "DP",
        "academic_dims": "Correctness, Accuracy",
        "detection": "Semi",
        "criticality": "ÉLEVÉ",
        "woodall": "SAST, SAMT",
        "algorithm": "Type analysis: Check precision loss (DECIMAL→INT)",
        "complexity": "O(1)",
    },
    "DP#7": {
        "name": "Troncatures de données",
        "description": "Données excédant longueur cible",
        "dimension": "DP",
        "academic_dims": "Completeness, Correctness",
        "detection": "Auto",
        "criticality": "MOYEN",
        "woodall": "SAST",
        "algorithm": "Length analysis: WHERE LENGTH(col) > max_length",
        "complexity": "O(1)",
    },
    "DP#8": {
        "name": "Conversions format dates",
        "description": "Parsing ambigu DD/MM vs MM/DD",
        "dimension": "DP",
        "academic_dims": "Correctness, Consistency",
        "detection": "Semi",
        "criticality": "CRITIQUE",
        "woodall": "SAST, MDS",
        "algorithm": "Format distribution: Detect ambiguous dates (day≤12)",
        "complexity": "O(n)",
    },
    "DP#9": {
        "name": "Problèmes de transcodage",
        "description": "Mapping référentiel source→cible incorrect",
        "dimension": "DP",
        "academic_dims": "Consistency, Correctness",
        "detection": "Semi",
        "criticality": "CRITIQUE",
        "woodall": "MR, MDS",
        "algorithm": "Domain analysis: Validate lookup table mappings",
        "complexity": "O(n)",
    },
    "DP#10": {
        "name": "Conversions unités mesure",
        "description": "Facteurs conversion erronés",
        "dimension": "DP",
        "academic_dims": "Correctness, Accuracy, Consistency",
        "detection": "Semi",
        "criticality": "CRITIQUE",
        "woodall": "SAST, SAMT, MDS",
        "algorithm": "Semantic profiling: Validate conversion factors",
        "complexity": "O(n)",
    },
    "DP#11": {
        "name": "Pertes lignes INNER JOIN",
        "description": "Cardinalité sortie < entrée",
        "dimension": "DP",
        "academic_dims": "Completeness, Correctness",
        "detection": "Semi",
        "criticality": "CRITIQUE",
        "woodall": "MR",
        "algorithm": "Cardinality analysis: COUNT(*) before vs after JOIN",
        "complexity": "O(n+m)",
    },
    "DP#12": {
        "name": "Duplications jointures 1-N",
        "description": "Explosion combinatoire JOIN",
        "dimension": "DP",
        "academic_dims": "Redundancy, Correctness",
        "detection": "Semi",
        "criticality": "CRITIQUE",
        "woodall": "MR",
        "algorithm": "Cardinality analysis: Detect one-to-many multiplier",
        "complexity": "O(n×m)",
    },
    "DP#13": {
        "name": "Clés jointure incorrectes",
        "description": "JOIN sur attribut non-unique",
        "dimension": "DP",
        "academic_dims": "Consistency, Correctness",
        "detection": "Manuel",
        "criticality": "CRITIQUE",
        "woodall": "MR",
        "algorithm": "PK/FK analysis: Check join key uniqueness (GAP partiel)",
        "complexity": "O(n)",
    },
    "DP#14": {
        "name": "Jointures cartésiennes",
        "description": "Produit cartésien accidentel (pas de ON)",
        "dimension": "DP",
        "academic_dims": "Redundancy, Correctness",
        "detection": "Auto",
        "criticality": "CRITIQUE",
        "woodall": "MR",
        "algorithm": "Cardinality analysis: Detect N×M explosion",
        "complexity": "O(n×m)",
    },
    "DP#15": {
        "name": "Fusion IDs conflictuels",
        "description": "Collision identifiants multi-sources",
        "dimension": "DP",
        "academic_dims": "Consistency, Correctness",
        "detection": "Semi",
        "criticality": "CRITIQUE",
        "woodall": "MDS",
        "algorithm": "Cross-domain analysis: Detect ID collisions across systems",
        "complexity": "O(n×s)\n s=nb sources",
    },
    "DP#16": {
        "name": "Conditions WHERE incorrectes",
        "description": "Prédicat excluant/incluant à tort",
        "dimension": "DP",
        "academic_dims": "Correctness, Relevance",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SAMT, SR",
        "algorithm": "Query analysis: Validate filter logic (requires business rules)",
        "complexity": "O(n)",
    },
    "DP#17": {
        "name": "Fenêtres temporelles incorrectes",
        "description": "Intervalles mal définis (bornes)",
        "dimension": "DP",
        "academic_dims": "Correctness, Timeliness",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SAMT, SR",
        "algorithm": "Temporal analysis: Check boundary conditions",
        "complexity": "O(n)",
    },
    "DP#18": {
        "name": "DISTINCT mal placé",
        "description": "Déduplication supprimant légitimes",
        "dimension": "DP",
        "academic_dims": "Redundancy, Correctness",
        "detection": "Semi",
        "criticality": "MOYEN",
        "woodall": "SAMT",
        "algorithm": "Query analysis: Detect DISTINCT before aggregation",
        "complexity": "O(n log n)",
    },
    "DP#19": {
        "name": "Erreurs GROUP BY",
        "description": "Agrégation sur mauvais niveau",
        "dimension": "DP",
        "academic_dims": "Correctness, Consistency",
        "detection": "Semi",
        "criticality": "ÉLEVÉ",
        "woodall": "SAMT, SR",
        "algorithm": "Semantic profiling: Validate GROUP BY completeness",
        "complexity": "O(n log n)",
    },
    "DP#20": {
        "name": "Données non chargées",
        "description": "Échec partiel chargement",
        "dimension": "DP",
        "academic_dims": "Completeness, Availability",
        "detection": "Semi",
        "criticality": "CRITIQUE",
        "woodall": "SR, MR, MDS",
        "algorithm": "Cardinality analysis: Compare expected vs loaded rows",
        "complexity": "O(n)",
    },
    "DP#21": {
        "name": "Ordre exécution incorrect",
        "description": "Séquence violant dépendances",
        "dimension": "DP",
        "academic_dims": "Correctness",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SR",
        "algorithm": "Dependency analysis: Check execution DAG (requires code inspection)",
        "complexity": "Manuel",
    },
    "DP#22": {
        "name": "Transformations non idempotentes",
        "description": "Réexécution modifie résultats",
        "dimension": "DP",
        "academic_dims": "Correctness, Consistency",
        "detection": "Manuel",
        "criticality": "ÉLEVÉ",
        "woodall": "SR",
        "algorithm": "Idempotency testing: Re-run and compare results",
        "complexity": "Manuel",
    },
    "DP#23": {
        "name": "Données obsolètes cache",
        "description": "Cache non invalidé après update",
        "dimension": "DP",
        "academic_dims": "Currency, Timeliness",
        "detection": "Semi",
        "criticality": "MOYEN",
        "woodall": "MR, MDS",
        "algorithm": "Timestamp analysis: Compare source vs cache freshness",
        "complexity": "O(n)",
    },
    "DP#24": {
        "name": "Échecs de propagation",
        "description": "Modifications source non propagées",
        "dimension": "DP",
        "academic_dims": "Completeness, Timeliness",
        "detection": "Semi",
        "criticality": "ÉLEVÉ",
        "woodall": "MR, MDS",
        "algorithm": "Lineage analysis: Track changes source→target",
        "complexity": "O(n)",
    },
    "DP#25": {
        "name": "Agrégations mauvaise granularité",
        "description": "Niveau temporel/spatial inadapté",
        "dimension": "DP",
        "academic_dims": "Relevance, Correctness",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SAMT, SR",
        "algorithm": "Semantic profiling: Validate aggregation granularity (requires business context)",
        "complexity": "O(n)",
    },
    "DP#26": {
        "name": "Valeurs pré-calculées obsolètes",
        "description": "Colonnes dénormalisées pas à jour",
        "dimension": "DP",
        "academic_dims": "Currency, Volatility",
        "detection": "Semi",
        "criticality": "MOYEN",
        "woodall": "MAST, SR",
        "algorithm": "Semantic profiling: Recalculate and compare",
        "complexity": "O(n)",
    },
    "DP#27": {
        "name": "Perte de granularité",
        "description": "Agrégation détruit info nécessaire",
        "dimension": "DP",
        "academic_dims": "Completeness, Relevance",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SAMT, SR",
        "algorithm": "Granularity analysis: Check if reversible (requires business rules)",
        "complexity": "O(n)",
    },
    "DP#28": {
        "name": "Fenêtres temps incorrectes agrégations",
        "description": "Périodes glissantes mal calculées",
        "dimension": "DP",
        "academic_dims": "Timeliness, Correctness",
        "detection": "Semi",
        "criticality": "MOYEN",
        "woodall": "SAMT, SR",
        "algorithm": "Temporal analysis: Validate rolling window logic",
        "complexity": "O(n)",
    },
    "DP#29": {
        "name": "Règles déduplication trop agressives",
        "description": "Fusion entités distinctes",
        "dimension": "DP",
        "academic_dims": "Correctness, Redundancy",
        "detection": "Manuel",
        "criticality": "ÉLEVÉ",
        "woodall": "SAMT, SR, MR",
        "algorithm": "Matching: Threshold tuning (precision vs recall trade-off)",
        "complexity": "O(n²) ou O(n×w)",
    },
    "DP#30": {
        "name": "Règles déduplication trop laxistes",
        "description": "Vrais doublons non détectés",
        "dimension": "DP",
        "academic_dims": "Redundancy, Correctness",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SAMT, SR, MR",
        "algorithm": "Matching: Threshold tuning (recall vs precision trade-off)",
        "complexity": "O(n²) ou O(n×w)",
    },
    "DP#31": {
        "name": "Choix master record incorrect",
        "description": "Stratégie survivorship inadaptée",
        "dimension": "DP",
        "academic_dims": "Correctness, Currency",
        "detection": "Manuel",
        "criticality": "ÉLEVÉ",
        "woodall": "SAMT, SR, MR",
        "algorithm": "Data consolidation: Survivorship rules (requires business rules)",
        "complexity": "O(n)",
    },
    "DP#32": {
        "name": "Perte historique déduplication",
        "description": "Fusion écrase versions temporelles",
        "dimension": "DP",
        "academic_dims": "Completeness, Timeliness",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SR, MR",
        "algorithm": "Data consolidation: Check temporal versioning preservation",
        "complexity": "O(n)",
    },
    "BR#1": {
        "name": "Incohérences temporelles",
        "description": "Relations ordre temporel violées",
        "dimension": "BR",
        "academic_dims": "Correctness, Consistency",
        "detection": "Auto",
        "criticality": "ÉLEVÉ",
        "woodall": "MAST",
        "algorithm": "Semantic profiling: WHERE date_fin < date_debut",
        "complexity": "O(1)",
        "frequency": "Fréquent",
    },
    "BR#2": {
        "name": "Valeurs hors bornes métier",
        "description": "Seuils business dépassés",
        "dimension": "BR",
        "academic_dims": "Validity, Correctness",
        "detection": "Auto",
        "criticality": "CRITIQUE",
        "woodall": "MAST",
        "algorithm": "Semantic profiling: WHERE prix_vente < cout_achat",
        "complexity": "O(1)",
        "frequency": "Fréquent",
    },
    "BR#3": {
        "name": "Combinaisons interdites",
        "description": "Paires/tuples mutuellement exclusifs",
        "dimension": "BR",
        "academic_dims": "Correctness, Validity",
        "detection": "Semi",
        "criticality": "ÉLEVÉ",
        "woodall": "MAST",
        "algorithm": "Semantic profiling: WHERE is_archived=true AND is_active=true",
        "complexity": "O(1)",
        "frequency": "Fréquent",
    },
    "BR#4": {
        "name": "Cardinalités métier violées",
        "description": "Contraintes multiplicité non respectées",
        "dimension": "BR",
        "academic_dims": "Completeness, Correctness",
        "detection": "Semi",
        "criticality": "MOYEN",
        "woodall": "MR",
        "algorithm": "Semantic profiling: Check business cardinality rules",
        "complexity": "O(n)",
        "frequency": "Occasionnel",
    },
    "BR#5": {
        "name": "Obligations métier non respectées",
        "description": "Attributs métier obligatoires absents",
        "dimension": "BR",
        "academic_dims": "Completeness",
        "detection": "Semi",
        "criticality": "ÉLEVÉ",
        "woodall": "MAST",
        "algorithm": "Semantic profiling: Business-required fields NULL",
        "complexity": "O(1)",
        "frequency": "Fréquent",
    },
    "BR#6": {
        "name": "Non-conformité protection données",
        "description": "Violations RGPD/CCPA",
        "dimension": "BR",
        "academic_dims": "Trust, Security (partiel)",
        "detection": "Manuel",
        "criticality": "CRITIQUE",
        "woodall": "MR, MDS",
        "algorithm": "Lineage analysis + consent tracking (requires legal expertise)",
        "complexity": "Manuel",
        "frequency": "Occasionnel",
    },
    "BR#7": {
        "name": "Non-conformité légale sectorielle",
        "description": "Violations réglementations spécifiques",
        "dimension": "BR",
        "academic_dims": "Trust, Correctness",
        "detection": "Manuel",
        "criticality": "CRITIQUE",
        "woodall": "MR, MDS",
        "algorithm": "Compliance analysis (requires domain expertise)",
        "complexity": "Manuel",
        "frequency": "Rare",
    },
    "BR#8": {
        "name": "Non-conformité fiscale/comptable",
        "description": "Violations IFRS/GAAP",
        "dimension": "BR",
        "academic_dims": "Trust, Correctness",
        "detection": "Manuel",
        "criticality": "CRITIQUE",
        "woodall": "MR",
        "algorithm": "Semantic profiling: Accounting rules validation (requires accounting expertise)",
        "complexity": "Manuel",
        "frequency": "Occasionnel",
    },
    "BR#9": {
        "name": "Non-conformité standards métier",
        "description": "Violations ISO/conventions",
        "dimension": "BR",
        "academic_dims": "Trust, Correctness",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "MR",
        "algorithm": "Compliance analysis: ISO/standards checking",
        "complexity": "Manuel",
        "frequency": "Occasionnel",
    },
    "BR#10": {
        "name": "Exigences audit non satisfaites",
        "description": "Traçabilité insuffisante",
        "dimension": "BR",
        "academic_dims": "Trust, Completeness",
        "detection": "Semi",
        "criticality": "ÉLEVÉ",
        "woodall": "SR, MR",
        "algorithm": "Audit trail analysis: Check WHO/WHEN/WHAT logs",
        "complexity": "O(n)",
        "frequency": "Fréquent",
    },
    "BR#11": {
        "name": "Incohérences calculés vs base",
        "description": "Redondances contradictoires",
        "dimension": "BR",
        "academic_dims": "Consistency, Correctness",
        "detection": "Auto",
        "criticality": "ÉLEVÉ",
        "woodall": "MAST",
        "algorithm": "Semantic profiling: WHERE montant_total <> SUM(lignes)",
        "complexity": "O(1)",
        "frequency": "Fréquent",
    },
    "BR#12": {
        "name": "Sommes de contrôle incorrectes",
        "description": "Checksums, balances ne concordent pas",
        "dimension": "BR",
        "academic_dims": "Correctness, Accuracy",
        "detection": "Auto",
        "criticality": "CRITIQUE",
        "woodall": "SAMT, SR",
        "algorithm": "Semantic profiling: SUM(debits) <> SUM(credits)",
        "complexity": "O(n)",
        "frequency": "Occasionnel",
    },
    "BR#13": {
        "name": "Ratios métier invalides",
        "description": "Métriques dérivées hors bornes",
        "dimension": "BR",
        "academic_dims": "Validity, Correctness",
        "detection": "Auto",
        "criticality": "MOYEN",
        "woodall": "MAST",
        "algorithm": "Semantic profiling: WHERE ratio > max_threshold",
        "complexity": "O(1)",
        "frequency": "Fréquent",
    },
    "BR#14": {
        "name": "Dépendances fonctionnelles violées",
        "description": "Règles if-then non respectées",
        "dimension": "BR",
        "academic_dims": "Consistency, Correctness",
        "detection": "Semi",
        "criticality": "ÉLEVÉ",
        "woodall": "MAST, SR",
        "algorithm": "Semantic profiling: Validate conditional rules",
        "complexity": "O(1) à O(n)",
        "frequency": "Fréquent",
    },
    "BR#15": {
        "name": "Exclusivité mutuelle violée",
        "description": "États incompatibles simultanés",
        "dimension": "BR",
        "academic_dims": "Consistency, Correctness",
        "detection": "Auto",
        "criticality": "ÉLEVÉ",
        "woodall": "MAST",
        "algorithm": "Semantic profiling: Check mutually exclusive states",
        "complexity": "O(1)",
        "frequency": "Fréquent",
    },
    "BR#16": {
        "name": "Hiérarchies incohérentes",
        "description": "Cycles, niveaux incorrects",
        "dimension": "BR",
        "academic_dims": "Consistency, Correctness",
        "detection": "Semi",
        "criticality": "ÉLEVÉ",
        "woodall": "SR",
        "algorithm": "Graph analysis: Cycle detection (DFS)",
        "complexity": "O(n×depth)",
        "frequency": "Occasionnel",
    },
    "BR#17": {
        "name": "Classifications métier incorrectes",
        "description": "Catégorisation invalide",
        "dimension": "BR",
        "academic_dims": "Validity, Correctness",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "MAST, MR",
        "algorithm": "Semantic profiling: Validate business taxonomy (requires domain knowledge)",
        "complexity": "O(1) à O(n)",
        "frequency": "Fréquent",
    },
    "BR#18": {
        "name": "Niveau hiérarchique incohérent",
        "description": "Position incompatible attributs",
        "dimension": "BR",
        "academic_dims": "Consistency, Correctness",
        "detection": "Semi",
        "criticality": "MOYEN",
        "woodall": "MAST, SR",
        "algorithm": "Semantic profiling: Validate hierarchy consistency",
        "complexity": "O(n)",
        "frequency": "Occasionnel",
    },
    "BR#19": {
        "name": "Appartenance multiple interdite",
        "description": "Entité dans classes exclusives",
        "dimension": "BR",
        "academic_dims": "Consistency, Correctness",
        "detection": "Auto",
        "criticality": "MOYEN",
        "woodall": "MAST",
        "algorithm": "Semantic profiling: Check exclusive class membership",
        "complexity": "O(1)",
        "frequency": "Rare",
    },
    "BR#20": {
        "name": "Changements niveau illogiques",
        "description": "Transitions impossibles/improbables",
        "dimension": "BR",
        "academic_dims": "Consistency, Correctness",
        "detection": "Manuel",
        "criticality": "FAIBLE",
        "woodall": "SR",
        "algorithm": "Transition analysis: Validate state machine (requires business rules)",
        "complexity": "O(n)",
        "frequency": "Rare",
    },
    "BR#21": {
        "name": "Politiques internes non respectées",
        "description": "Règles gouvernance violées",
        "dimension": "BR",
        "academic_dims": "Trust (partiel), Correctness",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "MAST, MR",
        "algorithm": "Policy compliance: Check against governance rules",
        "complexity": "O(n)",
        "frequency": "Fréquent",
    },
    "BR#22": {
        "name": "Seuils budgétaires dépassés",
        "description": "Limites dépenses excédées",
        "dimension": "BR",
        "academic_dims": "Validity, Correctness",
        "detection": "Semi",
        "criticality": "ÉLEVÉ",
        "woodall": "MAST, SR",
        "algorithm": "Semantic profiling: WHERE depenses > budget",
        "complexity": "O(n)",
        "frequency": "Fréquent",
    },
    "BR#23": {
        "name": "Processus approbation contournés",
        "description": "Workflows obligatoires non suivis",
        "dimension": "BR",
        "academic_dims": "Trust (partiel), Completeness",
        "detection": "Manuel",
        "criticality": "ÉLEVÉ",
        "woodall": "SR, MR",
        "algorithm": "Workflow analysis: Check approval chain completeness",
        "complexity": "O(n)",
        "frequency": "Occasionnel",
    },
    "BR#24": {
        "name": "Règles éligibilité non vérifiées",
        "description": "Conditions accès non contrôlées",
        "dimension": "BR",
        "academic_dims": "Correctness, Validity",
        "detection": "Semi",
        "criticality": "MOYEN",
        "woodall": "MAST, MR",
        "algorithm": "Semantic profiling: Validate eligibility criteria",
        "complexity": "O(1) à O(n)",
        "frequency": "Fréquent",
    },
    "BR#25": {
        "name": "Politiques sécurité violées",
        "description": "Habilitations incorrectes",
        "dimension": "BR",
        "academic_dims": "Security (partiel), Trust",
        "detection": "Manuel",
        "criticality": "CRITIQUE",
        "woodall": "MR, MDS",
        "algorithm": "Access control analysis: Check role-based permissions",
        "complexity": "O(n×r)\n r=nb roles",
        "frequency": "Occasionnel",
    },
    "BR#26": {
        "name": "Événements dans mauvais ordre",
        "description": "Séquence processus non respectée",
        "dimension": "BR",
        "academic_dims": "Correctness, Consistency",
        "detection": "Semi",
        "criticality": "ÉLEVÉ",
        "woodall": "SR",
        "algorithm": "Sequence analysis: Validate event ordering",
        "complexity": "O(n log n)",
        "frequency": "Fréquent",
    },
    "BR#27": {
        "name": "Délais réglementaires dépassés",
        "description": "Échéances légales non tenues",
        "dimension": "BR",
        "academic_dims": "Timeliness, Trust",
        "detection": "Semi",
        "criticality": "CRITIQUE",
        "woodall": "MAST, SR",
        "algorithm": "Temporal analysis: WHERE date_paiement > date_due + delai_legal",
        "complexity": "O(n)",
        "frequency": "Fréquent",
    },
    "BR#28": {
        "name": "Périodes validité incohérentes",
        "description": "Chevauchements/gaps interdits",
        "dimension": "BR",
        "academic_dims": "Consistency, Correctness",
        "detection": "Semi",
        "criticality": "MOYEN",
        "woodall": "SR",
        "algorithm": "Interval overlap detection",
        "complexity": "O(n log n)",
        "frequency": "Fréquent",
    },
    "BR#29": {
        "name": "Fréquence événements anormale",
        "description": "Occurrences trop/pas assez rapprochées",
        "dimension": "BR",
        "academic_dims": "Volatility (partiel), Correctness",
        "detection": "Semi",
        "criticality": "MOYEN",
        "woodall": "SR",
        "algorithm": "Frequency analysis: Detect anomalous event rates",
        "complexity": "O(n)",
        "frequency": "Occasionnel",
    },
    "BR#30": {
        "name": "Antériorité requise non respectée",
        "description": "Pré-requis temporel manquant",
        "dimension": "BR",
        "academic_dims": "Completeness, Correctness",
        "detection": "Semi",
        "criticality": "MOYEN",
        "woodall": "SR, MR",
        "algorithm": "Dependency analysis: Check prerequisite events exist",
        "complexity": "O(n)",
        "frequency": "Occasionnel",
    },
    "BR#31": {
        "name": "Dossiers incomplets",
        "description": "Ensemble documents métier partiel",
        "dimension": "BR",
        "academic_dims": "Completeness",
        "detection": "Manuel",
        "criticality": "ÉLEVÉ",
        "woodall": "MR",
        "algorithm": "Completeness analysis: Check required document set",
        "complexity": "O(n×d)\n d=nb docs requis",
        "frequency": "Très fréquent",
    },
    "BR#32": {
        "name": "Validations métier absentes",
        "description": "Certifications requises manquantes",
        "dimension": "BR",
        "academic_dims": "Completeness, Trust",
        "detection": "Manuel",
        "criticality": "ÉLEVÉ",
        "woodall": "MR",
        "algorithm": "Validation analysis: Check required certifications exist",
        "complexity": "O(n)",
        "frequency": "Fréquent",
    },
    "BR#33": {
        "name": "Documents justificatifs manquants",
        "description": "Pièces probantes absentes",
        "dimension": "BR",
        "academic_dims": "Completeness",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "MR",
        "algorithm": "Document linkage: Check supporting evidence exists",
        "complexity": "O(n)",
        "frequency": "Très fréquent",
    },
    "BR#34": {
        "name": "Approbations manquantes",
        "description": "Signatures/validations absentes",
        "dimension": "BR",
        "academic_dims": "Completeness, Trust",
        "detection": "Manuel",
        "criticality": "ÉLEVÉ",
        "woodall": "MR",
        "algorithm": "Approval analysis: Check signature/validation trails",
        "complexity": "O(n)",
        "frequency": "Fréquent",
    },
    "UP#1": {
        "name": "Granularité trop fine",
        "description": "Résolution excessive pour usage",
        "dimension": "UP",
        "academic_dims": "Relevance, Appropriate Amount",
        "detection": "Manuel",
        "criticality": "FAIBLE",
        "woodall": "MAST",
        "algorithm": "Usage profiling: Compare data resolution vs use case requirements",
        "complexity": "Manuel",
        "frequency": "Fréquent",
    },
    "UP#2": {
        "name": "Granularité trop large",
        "description": "Résolution insuffisante",
        "dimension": "UP",
        "academic_dims": "Relevance, Appropriate Amount",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "MAST",
        "algorithm": "Usage profiling: Check if aggregation loses required detail",
        "complexity": "Manuel",
        "frequency": "Fréquent",
    },
    "UP#3": {
        "name": "Niveau agrégation incorrect",
        "description": "Données agrégées/détaillées inadaptées",
        "dimension": "UP",
        "academic_dims": "Relevance, Appropriate Amount",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SAMT, SR",
        "algorithm": "Usage profiling: Match aggregation level to decision level",
        "complexity": "Manuel",
        "frequency": "Fréquent",
    },
    "UP#4": {
        "name": "Résolution temporelle inadaptée",
        "description": "Fréquence échantillonnage inappropriée",
        "dimension": "UP",
        "academic_dims": "Relevance, Timeliness",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SAMT, SR",
        "algorithm": "Temporal profiling: Compare sampling frequency vs volatility",
        "complexity": "Manuel",
        "frequency": "Fréquent",
    },
    "UP#5": {
        "name": "Résolution spatiale inadéquate",
        "description": "Découpage géographique inadapté",
        "dimension": "UP",
        "academic_dims": "Relevance, Appropriate Amount",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SAMT",
        "algorithm": "Spatial profiling: Match geographic resolution to use case",
        "complexity": "Manuel",
        "frequency": "Occasionnel",
    },
    "UP#6": {
        "name": "Données obsolètes",
        "description": "Âge > durée validité pour usage",
        "dimension": "UP",
        "academic_dims": "Currency, Timeliness",
        "detection": "Semi",
        "criticality": "ÉLEVÉ",
        "woodall": "SAMT",
        "algorithm": "Temporal analysis: WHERE last_update < NOW() - validity_period",
        "complexity": "O(n)",
        "frequency": "Très fréquent",
    },
    "UP#7": {
        "name": "Latence excessive",
        "description": "Délai capture→dispo > SLA",
        "dimension": "UP",
        "academic_dims": "Timeliness, Currency",
        "detection": "Semi",
        "criticality": "ÉLEVÉ",
        "woodall": "SR, MDS",
        "algorithm": "Temporal analysis: WHERE capture_time - availability_time > SLA",
        "complexity": "O(n)",
        "frequency": "Fréquent",
    },
    "UP#8": {
        "name": "Fréquence MAJ insuffisante",
        "description": "Période rafraîchissement > besoins",
        "dimension": "UP",
        "academic_dims": "Currency, Volatility, Timeliness",
        "detection": "Semi",
        "criticality": "MOYEN",
        "woodall": "SAMT, SR",
        "algorithm": "Temporal analysis: Compare refresh rate vs data volatility",
        "complexity": "O(n)",
        "frequency": "Fréquent",
    },
    "UP#9": {
        "name": "Données futures inappropriées",
        "description": "Prévisions pour usage nécessitant réalisé",
        "dimension": "UP",
        "academic_dims": "Relevance, Correctness",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "MAST",
        "algorithm": "Semantic profiling: Check if forecast used where actual required",
        "complexity": "Manuel",
        "frequency": "Occasionnel",
    },
    "UP#10": {
        "name": "Version donnée incorrecte",
        "description": "Snapshot temporel inadapté",
        "dimension": "UP",
        "academic_dims": "Currency, Timeliness",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SAMT",
        "algorithm": "Version analysis: Check snapshot date matches use case",
        "complexity": "Manuel",
        "frequency": "Occasionnel",
    },
    "UP#11": {
        "name": "Précision insuffisante",
        "description": "Décimales/chiffres significatifs inadéquats",
        "dimension": "UP",
        "academic_dims": "Accuracy, Relevance",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "MAST",
        "algorithm": "Precision analysis: Check significant digits match requirements",
        "complexity": "Manuel",
        "frequency": "Fréquent",
    },
    "UP#12": {
        "name": "Précision excessive",
        "description": "Fausse impression exactitude",
        "dimension": "UP",
        "academic_dims": "Accuracy (inverse), Relevance",
        "detection": "Manuel",
        "criticality": "FAIBLE",
        "woodall": "MAST",
        "algorithm": "Precision analysis: Check precision doesn't exceed data uncertainty",
        "complexity": "Manuel",
        "frequency": "Occasionnel",
    },
    "UP#13": {
        "name": "Marge erreur trop élevée",
        "description": "Incertitude inacceptable",
        "dimension": "UP",
        "academic_dims": "Accuracy, Trust",
        "detection": "Manuel",
        "criticality": "ÉLEVÉ",
        "woodall": "MAST",
        "algorithm": "Uncertainty analysis: Check error bounds vs decision threshold",
        "complexity": "Manuel",
        "frequency": "Occasionnel",
    },
    "UP#14": {
        "name": "Niveau confiance insuffisant",
        "description": "Fiabilité trop faible décision",
        "dimension": "UP",
        "academic_dims": "Trust, Reputation",
        "detection": "Manuel",
        "criticality": "CRITIQUE",
        "woodall": "SAMT, SR",
        "algorithm": "Confidence analysis: Check confidence level meets decision requirements",
        "complexity": "Manuel",
        "frequency": "Fréquent",
    },
    "UP#15": {
        "name": "Source non fiable pour usage",
        "description": "Provenance inadaptée exigence",
        "dimension": "UP",
        "academic_dims": "Trust, Reputation",
        "detection": "Manuel",
        "criticality": "ÉLEVÉ",
        "woodall": "MR, MDS",
        "algorithm": "Lineage analysis: Validate source trustworthiness for use case",
        "complexity": "Manuel",
        "frequency": "Fréquent",
    },
    "UP#16": {
        "name": "Taux remplissage insuffisant",
        "description": "Proportion NULL > seuil acceptable",
        "dimension": "UP",
        "academic_dims": "Completeness, Relevance",
        "detection": "Semi",
        "criticality": "ÉLEVÉ",
        "woodall": "SAMT",
        "algorithm": "Completeness analysis: WHERE COUNT(NULL)/COUNT(*) > threshold",
        "complexity": "O(n)",
        "frequency": "Très fréquent",
    },
    "UP#17": {
        "name": "Attributs manquants pour usage",
        "description": "Colonnes nécessaires absentes",
        "dimension": "UP",
        "academic_dims": "Completeness, Relevance",
        "detection": "Semi",
        "criticality": "ÉLEVÉ",
        "woodall": "MAST, MR",
        "algorithm": "Schema analysis: Check required attributes exist",
        "complexity": "O(1)",
        "frequency": "Fréquent",
    },
    "UP#18": {
        "name": "Périmètre incomplet",
        "description": "Couverture partielle univers métier",
        "dimension": "UP",
        "academic_dims": "Completeness, Appropriate Amount",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SR, MR",
        "algorithm": "Coverage analysis: Compare data universe vs business universe",
        "complexity": "O(n)",
        "frequency": "Fréquent",
    },
    "UP#19": {
        "name": "Historique insuffisant",
        "description": "Profondeur temporelle inadéquate",
        "dimension": "UP",
        "academic_dims": "Completeness, Appropriate Amount",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SR",
        "algorithm": "Temporal analysis: Check history depth vs analysis requirements",
        "complexity": "O(n)",
        "frequency": "Fréquent",
    },
    "UP#20": {
        "name": "Couverture géographique partielle",
        "description": "Zones géographiques manquantes",
        "dimension": "UP",
        "academic_dims": "Completeness, Appropriate Amount",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SAMT",
        "algorithm": "Geographic analysis: Check coverage vs required regions",
        "complexity": "O(n)",
        "frequency": "Occasionnel",
    },
    "UP#21": {
        "name": "Format inexploitable",
        "description": "Structure physique inadaptée",
        "dimension": "UP",
        "academic_dims": "Accessibility (partiel), Readability",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "MDS",
        "algorithm": "Format analysis: Check file format compatibility with use case",
        "complexity": "Manuel",
        "frequency": "Occasionnel",
    },
    "UP#22": {
        "name": "Granularité accès inadéquate",
        "description": "Niveau détail accessible ≠ requis",
        "dimension": "UP",
        "academic_dims": "Accessibility (partiel), Relevance",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SR, MR",
        "algorithm": "Access analysis: Check available detail vs required granularity",
        "complexity": "Manuel",
        "frequency": "Occasionnel",
    },
    "UP#23": {
        "name": "Données non interprétables",
        "description": "Codes sans métadonnées/référentiel",
        "dimension": "UP",
        "academic_dims": "Interpretability, Understandability",
        "detection": "Manuel",
        "criticality": "ÉLEVÉ",
        "woodall": "MR",
        "algorithm": "Metadata analysis: Check code dictionaries exist",
        "complexity": "Manuel",
        "frequency": "Très fréquent",
    },
    "UP#24": {
        "name": "Langue inappropriée",
        "description": "Langue naturelle inadaptée utilisateurs",
        "dimension": "UP",
        "academic_dims": "Understandability, Relevance",
        "detection": "Manuel",
        "criticality": "FAIBLE",
        "woodall": "SAMT",
        "algorithm": "Language analysis: Check data language matches user language",
        "complexity": "Manuel",
        "frequency": "Occasionnel",
    },
    "UP#25": {
        "name": "Encodage incompatible",
        "description": "Format technique inadapté environnement",
        "dimension": "UP",
        "academic_dims": "Accessibility (partiel), Readability",
        "detection": "Semi",
        "criticality": "MOYEN",
        "woodall": "MDS",
        "algorithm": "Encoding analysis: Check file encoding compatibility",
        "complexity": "O(n)",
        "frequency": "Rare",
    },
    "UP#26": {
        "name": "Périmètre trop large",
        "description": "Bruit informationnel (hors-sujet)",
        "dimension": "UP",
        "academic_dims": "Relevance, Appropriate Amount",
        "detection": "Manuel",
        "criticality": "FAIBLE",
        "woodall": "SR, MR",
        "algorithm": "Relevance analysis: Check for out-of-scope data",
        "complexity": "Manuel",
        "frequency": "Fréquent",
    },
    "UP#27": {
        "name": "Périmètre trop restreint",
        "description": "Vision tronquée phénomène",
        "dimension": "UP",
        "academic_dims": "Relevance, Completeness",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SR, MR",
        "algorithm": "Scope analysis: Check if data scope covers phenomenon",
        "complexity": "Manuel",
        "frequency": "Fréquent",
    },
    "UP#28": {
        "name": "Population cible incorrecte",
        "description": "Sous-ensemble inadapté question",
        "dimension": "UP",
        "academic_dims": "Relevance, Completeness",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SR",
        "algorithm": "Population analysis: Validate target population matches question",
        "complexity": "Manuel",
        "frequency": "Fréquent",
    },
    "UP#29": {
        "name": "Période temporelle inadaptée",
        "description": "Fenêtre temporelle inadéquate",
        "dimension": "UP",
        "academic_dims": "Relevance, Timeliness",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "SR",
        "algorithm": "Temporal analysis: Check time window matches analysis requirements",
        "complexity": "Manuel",
        "frequency": "Fréquent",
    },
    "UP#30": {
        "name": "Dimensions analytiques manquantes",
        "description": "Axes segmentation absents",
        "dimension": "UP",
        "academic_dims": "Relevance, Completeness",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "MR",
        "algorithm": "Dimensional analysis: Check required dimensions exist",
        "complexity": "Manuel",
        "frequency": "Fréquent",
    },
    "UP#31": {
        "name": "Définition ambiguë",
        "description": "Sens métier flou ou multiple",
        "dimension": "UP",
        "academic_dims": "Interpretability, Understandability, Validity",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "MAST",
        "algorithm": "Semantic analysis: Check definition clarity (requires metadata)",
        "complexity": "Manuel",
        "frequency": "Très fréquent",
    },
    "UP#32": {
        "name": "Unités non précisées",
        "description": "Unité de mesure non documentée",
        "dimension": "UP",
        "academic_dims": "Understandability, Interpretability",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "MAST",
        "algorithm": "Unit analysis: Check measurement units documented",
        "complexity": "Manuel",
        "frequency": "Très fréquent",
    },
    "UP#33": {
        "name": "Référentiel inadapté",
        "description": "Base comparaison/normalisation incorrecte",
        "dimension": "UP",
        "academic_dims": "Relevance, Validity",
        "detection": "Manuel",
        "criticality": "FAIBLE",
        "woodall": "MR",
        "algorithm": "Reference analysis: Check benchmark appropriateness",
        "complexity": "Manuel",
        "frequency": "Occasionnel",
    },
    "UP#34": {
        "name": "Contexte métier manquant",
        "description": "Métadonnées de contexte absentes",
        "dimension": "UP",
        "academic_dims": "Interpretability, Understandability",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "MR",
        "algorithm": "Metadata analysis: Check business context documented",
        "complexity": "Manuel",
        "frequency": "Très fréquent",
    },
    "UP#35": {
        "name": "Méthode calcul non documentée",
        "description": "Formule/algorithme non tracé",
        "dimension": "UP",
        "academic_dims": "Interpretability, Understandability",
        "detection": "Manuel",
        "criticality": "MOYEN",
        "woodall": "MAST, SR",
        "algorithm": "Lineage analysis: Check calculation method documented",
        "complexity": "Manuel",
        "frequency": "Fréquent",
    },
    "UP#36": {
        "name": "Données non conformes usage légal",
        "description": "Données non-certifiées finalité réglementaire",
        "dimension": "UP",
        "academic_dims": "Trust, Validity",
        "detection": "Manuel",
        "criticality": "CRITIQUE",
        "woodall": "MR, MDS",
        "algorithm": "Compliance analysis: Check data certification for legal use",
        "complexity": "Manuel",
        "frequency": "Occasionnel",
    },
    "UP#37": {
        "name": "Habilitation insuffisante",
        "description": "Droits accès inadaptés sensibilité",
        "dimension": "UP",
        "academic_dims": "Security (partiel), Trust",
        "detection": "Manuel",
        "criticality": "CRITIQUE",
        "woodall": "MR",
        "algorithm": "Access control analysis: Check user clearance vs data sensitivity",
        "complexity": "Manuel",
        "frequency": "Occasionnel",
    },
    "UP#38": {
        "name": "Traçabilité inadéquate",
        "description": "Piste audit insuffisante exigences",
        "dimension": "UP",
        "academic_dims": "Trust, Completeness",
        "detection": "Manuel",
        "criticality": "ÉLEVÉ",
        "woodall": "SR, MR",
        "algorithm": "Audit trail analysis: Check lineage completeness",
        "complexity": "Manuel",
        "frequency": "Fréquent",
    },
    "UP#39": {
        "name": "Durée conservation dépassée",
        "description": "Données conservées au-delà durée légale",
        "dimension": "UP",
        "academic_dims": "Trust (RGPD), Validity",
        "detection": "Semi",
        "criticality": "MOYEN",
        "woodall": "SAMT",
        "algorithm": "Retention analysis: WHERE retention_date < NOW() - legal_period",
        "complexity": "O(n)",
        "frequency": "Occasionnel",
    },
    "UP#40": {
        "name": "Finalité usage non autorisée",
        "description": "Utilisation hors consentement/finalité",
        "dimension": "UP",
        "academic_dims": "Trust (RGPD), Relevance",
        "detection": "Manuel",
        "criticality": "CRITIQUE",
        "woodall": "MDS",
        "algorithm": "Purpose analysis: Check data use matches collection purpose",
        "complexity": "Manuel",
        "frequency": "Rare",
    },
}


def get_by_dimension(dim: str) -> dict:
    """Retourne toutes les anomalies d'une dimension."""
    return _catalog.get_by_dimension(dim)


def get_auto_detectable() -> dict:
    """Retourne les anomalies détectables automatiquement."""
    return _catalog.get_auto_detectable()


def get_by_criticality(crit: str) -> dict:
    """Retourne les anomalies d'une criticité donnée."""
    return _catalog.get_by_criticality(crit)


def get_summary() -> dict:
    """Statistiques du référentiel."""
    summary = _catalog.get_summary()
    # Enrichir avec les compteurs de criticité pour rétrocompatibilité
    for dim, info in summary["by_dimension"].items():
        for crit in ("CRITIQUE", "ÉLEVÉ", "MOYEN", "FAIBLE"):
            if crit not in info:
                info[crit] = 0
        for aid, a in _catalog.anomalies.items():
            if a.get("dimension") == dim and a.get("criticality", "") in info:
                info[a["criticality"]] = info.get(a["criticality"], 0)
    # Recompter proprement
    by_dim = {}
    for a in REFERENTIAL.values():
        dim = a.get("dimension", "?")
        det = a.get("detection", "?")
        crit = a.get("criticality", "?")
        if dim not in by_dim:
            by_dim[dim] = {"total": 0, "Auto": 0, "Semi": 0, "Manuel": 0,
                           "CRITIQUE": 0, "ÉLEVÉ": 0, "MOYEN": 0, "FAIBLE": 0}
        by_dim[dim]["total"] += 1
        if det in by_dim[dim]:
            by_dim[dim][det] += 1
        if crit in by_dim[dim]:
            by_dim[dim][crit] += 1
    return {"total": len(REFERENTIAL), "by_dimension": by_dim}
