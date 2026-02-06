# Diagrammes d'Architecture - Framework DQ Probabiliste

> Ces diagrammes utilisent la syntaxe Mermaid, supportée nativement par GitHub.

## 1. Vue Contexte (C4 - Level 1)

```mermaid
C4Context
    title Contexte Système - Framework Data Quality Probabiliste

    Person(analyst, "Data Analyst", "Analyse et améliore la qualité des données")

    System(dqframework, "Framework DQ Probabiliste", "Application web d'analyse de qualité des données avec approche probabiliste 4D")

    System_Ext(claude, "Claude API", "API Anthropic pour génération de rapports et explications IA")
    System_Ext(github, "GitHub", "Hébergement code source et CI/CD")
    System_Ext(streamlit_cloud, "Streamlit Cloud", "Plateforme d'hébergement")

    Rel(analyst, dqframework, "Utilise", "HTTPS")
    Rel(dqframework, claude, "Requêtes IA", "HTTPS/API")
    Rel(github, streamlit_cloud, "Déploiement auto", "Webhook")
```

## 2. Architecture Container (C4 - Level 2)

```mermaid
C4Container
    title Architecture Container - Framework DQ

    Person(user, "Utilisateur", "Data Analyst / DPO / DSI")

    Container_Boundary(app, "Framework DQ Probabiliste") {
        Container(frontend, "Frontend Streamlit", "Python/Streamlit", "Interface utilisateur avec 12 onglets")
        Container(backend, "Backend Engine", "Python", "Moteur de calcul probabiliste")
        Container(security, "Security Module", "Python", "Validation, sanitization, auth")
        Container(audit, "Audit Trail", "Python/JSON", "Traçabilité complète")
    }

    System_Ext(claude_api, "Claude API", "LLM Anthropic")
    System_Ext(storage, "Session State", "Mémoire Streamlit")

    Rel(user, frontend, "Interagit", "HTTPS")
    Rel(frontend, backend, "Appelle", "Import Python")
    Rel(frontend, security, "Valide", "Import Python")
    Rel(frontend, audit, "Log", "Import Python")
    Rel(frontend, claude_api, "Requêtes IA", "HTTPS")
    Rel(frontend, storage, "Stocke", "Session")
```

## 3. Architecture Composants (C4 - Level 3)

```mermaid
flowchart TB
    subgraph Frontend["🖥️ Frontend (Streamlit)"]
        app[app.py<br/>Orchestrateur]
        css[streamlit_gray_css.py<br/>Styles]
        scan[streamlit_anomaly_detection.py<br/>Scan]
        audit_tab[streamlit_audit_tab.py<br/>Historique]
    end

    subgraph Backend["⚙️ Backend"]
        subgraph Engine["Engine"]
            analyzer[analyzer.py<br/>Analyse Stats]
            beta[beta_calculator.py<br/>Vecteurs 4D]
            ahp[ahp_elicitor.py<br/>Pondération]
            scorer[risk_scorer.py<br/>Scoring]
            comparator[comparator.py<br/>DAMA vs 4D]
            lineage[lineage_propagator.py<br/>Propagation]
        end

        subgraph Catalogs["Catalogs"]
            core[core_anomaly_catalog.py<br/>30 règles]
            extended[extended_anomaly_catalog.py<br/>30+ règles]
        end
    end

    subgraph Transverse["🔐 Transverse"]
        security[security.py<br/>Sécurité]
        audit[audit_trail.py<br/>Audit]
    end

    app --> css
    app --> scan
    app --> audit_tab
    app --> analyzer
    app --> beta
    app --> ahp
    app --> scorer
    app --> comparator
    app --> lineage
    app --> security
    app --> audit

    scan --> core
    scan --> extended
    beta --> core
    beta --> extended
```

## 4. Flux de Données Principal

```mermaid
flowchart LR
    subgraph Input["📥 Entrée"]
        file[Fichier<br/>CSV/Excel]
    end

    subgraph Validation["🔒 Validation"]
        v1[Taille < 50MB]
        v2[MIME Type]
        v3[Sanitization]
        v4[Hash SHA-256]
    end

    subgraph Analysis["🔍 Analyse"]
        a1[Statistiques]
        a2[Détection<br/>Anomalies]
        a3[Vecteurs 4D]
    end

    subgraph Scoring["📊 Scoring"]
        s1[Pondération AHP]
        s2[Calcul Scores]
        s3[Priorisation]
    end

    subgraph Output["📤 Sortie"]
        o1[Dashboard]
        o2[Rapports IA]
        o3[Exports]
    end

    file --> v1 --> v2 --> v3 --> v4
    v4 --> a1 --> a2 --> a3
    a3 --> s1 --> s2 --> s3
    s3 --> o1 & o2 & o3
```

## 5. Modèle Probabiliste 4D

```mermaid
flowchart TB
    subgraph Vecteur4D["🎯 Vecteur Probabiliste 4D"]
        direction LR
        P_DB["P_DB<br/>📦 Structure<br/>(Database)"]
        P_DP["P_DP<br/>⚙️ Traitements<br/>(Data Processing)"]
        P_BR["P_BR<br/>📋 Règles Métier<br/>(Business Rules)"]
        P_UP["P_UP<br/>🎯 Adéquation<br/>(Usage-fit Purpose)"]
    end

    subgraph Sources["Sources de Risque"]
        nulls[Valeurs Nulles]
        types[Types Incohérents]
        formats[Formats Invalides]
        outliers[Outliers]
        patterns[Patterns Métier]
        ranges[Plages Invalides]
        context[Contexte Usage]
        critical[Criticité]
    end

    nulls & types --> P_DB
    formats & outliers --> P_DP
    patterns & ranges --> P_BR
    context & critical --> P_UP

    subgraph Score["Score Final"]
        formula["Score = Σ(w_i × P_i) × multiplicateur"]
    end

    P_DB & P_DP & P_BR & P_UP --> formula
```

## 6. Mapping DAMA ↔ 4D

```mermaid
flowchart LR
    subgraph DAMA["📐 Dimensions DAMA"]
        completeness[Complétude]
        uniqueness[Unicité]
        validity[Validité]
        consistency[Cohérence]
        timeliness[Fraîcheur]
        accuracy[Exactitude]
    end

    subgraph Probabiliste["🎯 Vecteurs 4D"]
        P_DB["P_DB"]
        P_DP["P_DP"]
        P_BR["P_BR"]
        P_UP["P_UP"]
    end

    completeness --> P_DB
    uniqueness --> P_DB
    validity --> P_BR
    consistency --> P_BR
    timeliness --> P_DP
    accuracy --> P_UP
```

## 7. Architecture de Sécurité

```mermaid
flowchart TB
    subgraph Input["🔐 Couche Entrée"]
        file_val["Validation Fichier<br/>• Taille<br/>• MIME<br/>• Extension"]
        input_san["Sanitization Input<br/>• XSS<br/>• SQL Injection<br/>• Max Length"]
        api_val["Validation API Key<br/>• Format sk-ant-<br/>• Masquage"]
    end

    subgraph Auth["🔑 Authentification"]
        secrets["secrets.toml<br/>(chiffré)"]
        admin["Admin Auth<br/>• Password<br/>• Session State"]
    end

    subgraph Output["🛡️ Couche Sortie"]
        html_esc["HTML Escape<br/>• sanitize_column_name<br/>• escape_html"]
        error_safe["Safe Errors<br/>• No stack trace<br/>• Generic messages"]
        audit_log["Audit Trail<br/>• Horodatage<br/>• Hash fichiers"]
    end

    Input --> Auth --> Output
```

## 8. Architecture de Déploiement

```mermaid
flowchart TB
    subgraph User["👤 Utilisateur"]
        browser[Navigateur Web]
    end

    subgraph Cloud["☁️ Streamlit Cloud"]
        lb[Load Balancer<br/>SSL Termination]
        container[Container Runtime<br/>Python 3.11]
        secrets[Secrets Manager]
        session[Session State]
    end

    subgraph External["🌐 Services Externes"]
        github[GitHub<br/>momsarew/augmented-dq-demo]
        anthropic[Anthropic API<br/>Claude Sonnet 4]
    end

    browser -->|HTTPS| lb
    lb --> container
    container --> secrets
    container --> session
    container -->|API| anthropic
    github -->|Deploy| container
```

## 9. Diagramme de Séquence - Analyse

```mermaid
sequenceDiagram
    actor User
    participant UI as Frontend
    participant Sec as Security
    participant Eng as Engine
    participant Audit as AuditTrail
    participant AI as Claude API

    User->>UI: Upload CSV/Excel
    UI->>Sec: validate_uploaded_file()
    Sec-->>UI: ✓ Valid
    UI->>Audit: log_file_upload()

    User->>UI: Select columns + usages
    User->>UI: Click ANALYSE

    UI->>Eng: analyze_dataset()
    Eng-->>UI: stats

    UI->>Eng: compute_all_beta_vectors()
    Eng-->>UI: vecteurs 4D

    UI->>Eng: compute_risk_scores()
    Eng-->>UI: scores

    UI->>Audit: log_analysis()
    UI->>Audit: log_calculation()

    UI-->>User: Affiche résultats

    opt Demande explication IA
        User->>UI: Click "Expliquer"
        UI->>AI: messages.create()
        AI-->>UI: explanation
        UI->>Audit: log_ai_request()
        UI-->>User: Affiche explication
    end
```

## 10. États de l'Application

```mermaid
stateDiagram-v2
    [*] --> Accueil

    Accueil --> FileUploaded: Upload fichier
    FileUploaded --> ColumnsSelected: Sélection colonnes
    ColumnsSelected --> UsagesSelected: Sélection usages
    UsagesSelected --> Analyzing: Click ANALYSE

    Analyzing --> AnalysisDone: Succès
    Analyzing --> Error: Erreur

    Error --> FileUploaded: Retry

    state AnalysisDone {
        [*] --> Dashboard
        Dashboard --> Vecteurs
        Vecteurs --> Priorites
        Priorites --> Elicitation
        Elicitation --> ProfilRisque
        ProfilRisque --> Lineage
        Lineage --> DAMA
        DAMA --> Reporting
        Reporting --> Historique
        Historique --> Parametres
    }

    AnalysisDone --> Accueil: Reset
```

---

## Légende

| Symbole | Signification |
|---------|---------------|
| 📥 | Entrée de données |
| 📤 | Sortie de données |
| 🔐 | Sécurité |
| 🎯 | Scoring/Ciblage |
| ⚙️ | Traitement |
| 📊 | Analyse/Dashboard |
| 🤖 | Intelligence Artificielle |

---

*Généré le 2025-02-06 - Version 1.2.0*
