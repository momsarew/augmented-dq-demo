"""
API FastAPI - Framework Probabiliste DQ
Endpoints pour analyse datasets, calculs Beta, scores risque, etc.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import json
import io
import time

# Import moteur
import sys
sys.path.append('/home/claude/backend')

from engine import (
    analyze_dataset,
    compute_all_beta_vectors,
    elicit_weights_auto,
    compute_risk_scores,
    get_top_priorities,
    simulate_lineage,
    compare_dama_vs_probabiliste
)


# ============================================================================
# CONFIGURATION API
# ============================================================================

app = FastAPI(
    title="Framework DQ Probabiliste API",
    description="API pour calculs qualité données probabilistes bayésiens",
    version="1.0.0"
)

# CORS (autoriser Lovable frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod: restreindre à domaine Lovable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# MODÈLES PYDANTIC (Validation requêtes)
# ============================================================================

class AnalyzeRequest(BaseModel):
    """
    Requête analyse complète dataset
    """
    data: Dict[str, Any]  # {"rows": [...], "columns": [...]}
    columns_to_analyze: List[str]
    usages: List[Dict[str, Any]]  # [{"nom": "Paie", "type": "paie_reglementaire", ...}]
    
    class Config:
        schema_extra = {
            "example": {
                "data": {
                    "rows": [
                        {"Anciennete": "7,21", "LEVEL_ACN": "MGR7"},
                        {"Anciennete": "3,45", "LEVEL_ACN": "CON9"}
                    ],
                    "columns": ["Anciennete", "LEVEL_ACN"]
                },
                "columns_to_analyze": ["Anciennete", "LEVEL_ACN"],
                "usages": [
                    {"nom": "Paie", "type": "paie_reglementaire", "criticite": "HIGH"}
                ]
            }
        }


class ChatRequest(BaseModel):
    """
    Requête chat élicitation IA
    """
    message: str
    context: Dict[str, Any]  # État conversation


class StatsRequest(BaseModel):
    """
    Requête stats exploratoires seules
    """
    data: Dict[str, Any]
    columns: List[str]


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """
    Health check racine
    """
    return {
        "status": "ok",
        "service": "Framework DQ Probabiliste API",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/api/analyze",
            "/api/analyze/stats",
            "/api/upload"
        ]
    }


@app.get("/health")
async def health_check():
    """
    Health check détaillé
    """
    return {
        "status": "healthy",
        "engine_version": "1.0.0",
        "modules": [
            "analyzer",
            "beta_calculator",
            "ahp_elicitor",
            "risk_scorer",
            "lineage_propagator",
            "comparator"
        ],
        "timestamp": time.time()
    }


@app.post("/api/analyze")
async def analyze_full(request: AnalyzeRequest):
    """
    ENDPOINT PRINCIPAL - Analyse complète dataset
    
    Étapes:
    1. Stats exploratoires
    2. Calcul vecteurs 4D (Beta)
    3. Élicitation pondérations AHP
    4. Scores risque contextualisés
    5. Simulation lineage (optionnelle)
    6. Comparaison DAMA
    
    Returns:
        {
            "status": "success",
            "stats": {...},
            "vecteurs_4d": {...},
            "weights": {...},
            "scores": {...},
            "top_priorities": [...],
            "lineage": {...},
            "comparaison_dama": {...},
            "execution_time_ms": 1234
        }
    """
    start_time = time.time()
    
    try:
        # 1. Parser données
        df = pd.DataFrame(request.data['rows'])
        columns = request.columns_to_analyze
        usages = request.usages
        
        # 2. Analyse exploratoire
        stats = analyze_dataset(df, columns)
        
        # 3. Calcul vecteurs 4D
        vecteurs_4d = compute_all_beta_vectors(df, columns, stats)
        
        # 4. Élicitation pondérations
        weights = elicit_weights_auto(usages, vecteurs_4d)
        
        # 5. Scores risque
        scores = compute_risk_scores(vecteurs_4d, weights, usages)
        
        # 6. Top priorités
        top_priorities = get_top_priorities(scores, top_n=5)
        
        # 7. Simulation lineage (premier attribut, premier usage)
        lineage = None
        if len(columns) > 0 and len(usages) > 0:
            first_attr = columns[0]
            first_usage = usages[0]['nom']
            
            if first_attr in vecteurs_4d and first_usage in weights:
                lineage = simulate_lineage(
                    vecteurs_4d[first_attr],
                    weights[first_usage]
                )
        
        # 8. Comparaison DAMA
        comparaison = compare_dama_vs_probabiliste(
            df, columns, scores, vecteurs_4d
        )
        
        # Temps exécution
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        return {
            "status": "success",
            "stats": stats,
            "vecteurs_4d": vecteurs_4d,
            "weights": weights,
            "scores": scores,
            "top_priorities": top_priorities,
            "lineage": lineage,
            "comparaison_dama": comparaison,
            "execution_time_ms": execution_time_ms,
            "metadata": {
                "n_rows": len(df),
                "n_columns": len(columns),
                "n_usages": len(usages)
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur analyse: {str(e)}"
        )


@app.post("/api/analyze/stats")
async def analyze_stats_only(request: StatsRequest):
    """
    Stats exploratoires uniquement (rapide)
    """
    try:
        df = pd.DataFrame(request.data['rows'])
        stats = analyze_dataset(df, request.columns)
        
        return {
            "status": "success",
            "stats": stats
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur stats: {str(e)}"
        )


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload fichier CSV/Excel et analyse automatique
    
    Returns:
        {
            "status": "success",
            "filename": "data.csv",
            "preview": {...},
            "columns": [...],
            "suggested_columns": [...]
        }
    """
    try:
        # Lire fichier
        contents = await file.read()
        
        # Parser selon extension
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(
                status_code=400,
                detail="Format non supporté. Utiliser CSV ou Excel."
            )
        
        # Preview données
        preview = {
            "n_rows": len(df),
            "n_columns": len(df.columns),
            "columns": df.columns.tolist(),
            "sample": df.head(5).to_dict(orient='records'),
            "dtypes": df.dtypes.astype(str).to_dict()
        }
        
        # Suggestions colonnes critiques (heuristiques)
        suggested_columns = []
        for col in df.columns:
            col_lower = col.lower()
            # Patterns RH critiques
            if any(kw in col_lower for kw in ['anciennete', 'salaire', 'date', 'level', 'matricule', 'prime']):
                suggested_columns.append(col)
        
        return {
            "status": "success",
            "filename": file.filename,
            "preview": preview,
            "suggested_columns": suggested_columns
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur upload: {str(e)}"
        )


@app.post("/api/chat/elicit")
async def chat_elicitation(request: ChatRequest):
    """
    Dialogue IA élicitation assistée
    
    NOTE: Version rule-based pour démo
    En prod, intégrer LLM (GPT-4/Claude)
    """
    user_message = request.message.lower()
    context = request.context
    
    # Analyse intent basique
    if "ok pour db" in user_message or "valider db" in user_message:
        return {
            "ia_response": "✅ [DB] Database validé. Passons à [DP] Data Processing...",
            "action": "validate_dimension",
            "dimension": "DB",
            "next_question": "Y a-t-il des transformations complexes dans vos pipelines ETL ?"
        }
    
    elif "violations" in user_message and "dirigeants" in user_message:
        return {
            "ia_response": "Compris ! Violations légitimes (dirigeants) exclues du calcul.",
            "action": "adjust_beta",
            "dimension": "BR",
            "adjustment": "exclude_legitimate_violations",
            "new_beta": {"alpha": 1, "beta": 686}
        }
    
    elif "ajoute usage" in user_message or "ajouter usage" in user_message:
        return {
            "ia_response": "Quel est le nom du nouvel usage métier à ajouter ?",
            "action": "add_usage",
            "awaiting_input": "usage_name"
        }
    
    else:
        # Fallback générique
        return {
            "ia_response": "Je n'ai pas compris. Pouvez-vous reformuler ou choisir parmi : "
                          "[Valider dimension] [Ajuster paramètres] [Ajouter usage]",
            "action": "clarification_needed"
        }


# ============================================================================
# ENDPOINTS UTILITAIRES
# ============================================================================

@app.get("/api/usages/presets")
async def get_usage_presets():
    """
    Retourne usages pré-configurés
    """
    from engine.ahp_elicitor import AHPElicitor
    
    elicitor = AHPElicitor()
    
    return {
        "presets": {
            key: {
                **value,
                "key": key,
                "display_name": key.replace('_', ' ').title()
            }
            for key, value in elicitor.PRESET_WEIGHTS.items()
        }
    }


@app.get("/api/examples/dataset")
async def get_example_dataset():
    """
    Retourne dataset exemple pour tests
    """
    # Dataset RH simplifié
    df_example = pd.DataFrame({
        'Anciennete': ['7,21', '3,45', '12,08', '5,67'] * 50,  # 200 lignes
        'Dates_promos': [None] * 80 + ['01/01/2020', '15/06/2021'] * 60,
        'LEVEL_ACN': ['MGR7', 'CON9', 'AN10', 'SMR6'] * 50
    })
    
    return {
        "data": {
            "rows": df_example.to_dict(orient='records'),
            "columns": df_example.columns.tolist()
        },
        "suggested_config": {
            "columns_to_analyze": ["Anciennete", "Dates_promos", "LEVEL_ACN"],
            "usages": [
                {"nom": "Paie", "type": "paie_reglementaire", "criticite": "HIGH"},
                {"nom": "CSE", "type": "reporting_social", "criticite": "MEDIUM"}
            ]
        }
    }


# ============================================================================
# DÉMARRAGE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("="*80)
    print("🚀 DÉMARRAGE API FRAMEWORK PROBABILISTE DQ")
    print("="*80)
    print("URL: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("="*80)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
