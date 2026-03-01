"""Claude AI explanation helper."""

import json
import streamlit as st


def explain_with_ai(scope, data, cache_key, max_tokens=400):
    """Call Claude API to generate contextual explanations."""
    if cache_key in st.session_state.ai_explanations:
        return st.session_state.ai_explanations[cache_key]

    api_key = st.session_state.get("anthropic_api_key", "").strip()
    if not api_key:
        return "Configurez la cle API Claude dans la sidebar"

    if not api_key.startswith("sk-ant-"):
        return "Cle API invalide (doit commencer par 'sk-ant-')"

    prompts = {
        "vector": "Explique vecteur 4D en 3 phrases : dimension critique, cause, action.",
        "priority": "Explique priorité en 3 phrases : pourquoi, impact, action.",
        "lineage": "Explique propagation risque en 3 phrases : aggravation, étape, gain.",
        "dama": "Compare DAMA vs Probabiliste en 3 phrases : limites, avantage, ROI.",
        "global": "Synthèse dashboard en 4 phrases : situation, critiques, actions.",
        "elicitation": "Explique ces pondérations en 3 phrases : justification métier, impact sur calculs, recommandations.",
    }

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=prompts.get(scope, prompts["global"]),
            messages=[{"role": "user", "content": json.dumps({"scope": scope, "data": data})}],
        )
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        st.session_state.ai_tokens_used += tokens_used
        explanation = response.content[0].text
        st.session_state.ai_explanations[cache_key] = explanation

        # Audit logging
        try:
            from backend.audit_trail import get_audit_trail
            audit = get_audit_trail()
            audit.log_ai_request(
                request_type=f"explanation_{scope}",
                prompt_summary=f"Explication pour {scope}",
                tokens_used=tokens_used,
                success=True,
                response_summary=explanation[:100] if explanation else None
            )
        except Exception:
            pass

        return explanation
    except Exception as e:
        if "AuthenticationError" in type(e).__name__:
            return "Erreur authentification : verifiez la cle API"
        if "RateLimitError" in type(e).__name__:
            return "Limite de taux atteinte : reessayez dans quelques secondes"
        return f"Erreur : {str(e)[:200]}"
