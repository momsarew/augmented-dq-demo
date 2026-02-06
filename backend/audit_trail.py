"""
Audit Trail - Système de traçabilité complet pour l'application Data Quality
Enregistre toutes les actions, calculs et événements avec horodatage
"""

import os
import json
import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import pandas as pd


class AuditTrail:
    """
    Gestionnaire d'audit trail pour tracer toutes les opérations.

    Fonctionnalités:
    - Horodatage précis de chaque action
    - Hash des fichiers pour intégrité
    - Détail des calculs (paramètres, résultats)
    - Persistance JSON entre sessions
    - Export CSV/JSON
    - Filtrage et recherche
    """

    # Types d'événements
    EVENT_TYPES = {
        "FILE_UPLOAD": "📁 Upload fichier",
        "FILE_EXPORT": "📤 Export fichier",
        "ANALYSIS": "🔍 Analyse",
        "CALCULATION": "🧮 Calcul",
        "SCORE": "📊 Score",
        "DAMA": "📐 DAMA",
        "AHP": "⚖️ Pondération AHP",
        "PROFILE": "👤 Profil",
        "LINEAGE": "🔗 Lignage",
        "AI_REQUEST": "🤖 Requête IA",
        "REPORT": "📋 Rapport",
        "CONFIG": "⚙️ Configuration",
        "ADMIN": "🔐 Admin",
        "ERROR": "❌ Erreur",
        "SESSION": "🚀 Session",
    }

    # Niveaux de sévérité
    SEVERITY_LEVELS = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🚨",
    }

    def __init__(self,
                 storage_path: Optional[str] = None,
                 max_memory_events: int = 1000,
                 auto_persist: bool = True):
        """
        Initialise l'audit trail.

        Args:
            storage_path: Chemin du fichier JSON pour persistance
            max_memory_events: Nombre max d'événements en mémoire
            auto_persist: Sauvegarder automatiquement après chaque événement
        """
        self.session_id = str(uuid.uuid4())[:8]
        self.session_start = datetime.now()
        self.events: List[Dict[str, Any]] = []
        self.max_memory_events = max_memory_events
        self.auto_persist = auto_persist

        # Chemin de stockage
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            # Défaut: dossier .audit dans le projet
            project_dir = Path(__file__).parent.parent
            audit_dir = project_dir / ".audit"
            audit_dir.mkdir(exist_ok=True)
            self.storage_path = audit_dir / "audit_trail.json"

        # Charger l'historique existant
        self._load_from_storage()

        # Enregistrer le démarrage de session
        self.log_event(
            event_type="SESSION",
            action="session_start",
            description="Nouvelle session démarrée",
            severity="INFO",
            details={"session_id": self.session_id}
        )

    def _generate_event_id(self) -> str:
        """Génère un ID unique pour l'événement"""
        return f"{self.session_id}-{len(self.events):04d}-{uuid.uuid4().hex[:6]}"

    def _get_timestamp(self) -> str:
        """Retourne le timestamp actuel au format ISO"""
        return datetime.now().isoformat()

    def compute_file_hash(self, file_content: bytes) -> str:
        """
        Calcule le hash SHA-256 d'un fichier pour vérifier l'intégrité.

        Args:
            file_content: Contenu du fichier en bytes

        Returns:
            Hash SHA-256 du fichier
        """
        return hashlib.sha256(file_content).hexdigest()

    def compute_dataframe_hash(self, df: pd.DataFrame) -> str:
        """
        Calcule un hash du DataFrame pour traçabilité.

        Args:
            df: DataFrame pandas

        Returns:
            Hash basé sur le contenu du DataFrame
        """
        # Créer une représentation stable du DataFrame
        content = f"{df.shape}|{list(df.columns)}|{df.values.tobytes()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def log_event(self,
                  event_type: str,
                  action: str,
                  description: str,
                  severity: str = "INFO",
                  details: Optional[Dict[str, Any]] = None,
                  user: Optional[str] = None,
                  file_hash: Optional[str] = None) -> str:
        """
        Enregistre un événement dans l'audit trail.

        Args:
            event_type: Type d'événement (voir EVENT_TYPES)
            action: Action spécifique effectuée
            description: Description lisible de l'événement
            severity: Niveau de sévérité (INFO, SUCCESS, WARNING, ERROR, CRITICAL)
            details: Détails supplémentaires (paramètres, résultats, etc.)
            user: Identifiant utilisateur (optionnel)
            file_hash: Hash du fichier concerné (optionnel)

        Returns:
            ID de l'événement créé
        """
        event_id = self._generate_event_id()

        event = {
            "id": event_id,
            "timestamp": self._get_timestamp(),
            "session_id": self.session_id,
            "event_type": event_type,
            "event_type_label": self.EVENT_TYPES.get(event_type, event_type),
            "action": action,
            "description": description,
            "severity": severity,
            "severity_icon": self.SEVERITY_LEVELS.get(severity, ""),
            "details": details or {},
            "user": user,
            "file_hash": file_hash,
        }

        self.events.append(event)

        # Limiter la taille en mémoire
        if len(self.events) > self.max_memory_events:
            self.events = self.events[-self.max_memory_events:]

        # Sauvegarder automatiquement
        if self.auto_persist:
            self._save_to_storage()

        return event_id

    # =========================================================================
    # MÉTHODES DE LOG SPÉCIALISÉES
    # =========================================================================

    def log_file_upload(self,
                        filename: str,
                        file_size: int,
                        file_hash: str,
                        rows: int,
                        columns: int,
                        column_names: List[str]) -> str:
        """Log un upload de fichier"""
        return self.log_event(
            event_type="FILE_UPLOAD",
            action="upload",
            description=f"Fichier '{filename}' uploadé ({rows} lignes, {columns} colonnes)",
            severity="SUCCESS",
            file_hash=file_hash,
            details={
                "filename": filename,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "rows": rows,
                "columns": columns,
                "column_names": column_names[:20],  # Limiter pour lisibilité
            }
        )

    def log_analysis(self,
                     analysis_type: str,
                     columns_analyzed: List[str],
                     results_summary: Dict[str, Any],
                     duration_ms: Optional[float] = None) -> str:
        """Log une analyse de données"""
        return self.log_event(
            event_type="ANALYSIS",
            action=analysis_type,
            description=f"Analyse '{analysis_type}' sur {len(columns_analyzed)} colonnes",
            severity="SUCCESS",
            details={
                "analysis_type": analysis_type,
                "columns_analyzed": columns_analyzed,
                "results_summary": results_summary,
                "duration_ms": duration_ms,
            }
        )

    def log_calculation(self,
                        calculation_type: str,
                        column: str,
                        parameters: Dict[str, Any],
                        results: Dict[str, Any],
                        duration_ms: Optional[float] = None) -> str:
        """Log un calcul (vecteurs beta, scores, etc.)"""
        return self.log_event(
            event_type="CALCULATION",
            action=calculation_type,
            description=f"Calcul '{calculation_type}' pour colonne '{column}'",
            severity="SUCCESS",
            details={
                "calculation_type": calculation_type,
                "column": column,
                "parameters": parameters,
                "results": self._sanitize_results(results),
                "duration_ms": duration_ms,
            }
        )

    def log_score(self,
                  score_type: str,
                  column: str,
                  score_value: float,
                  weights: Dict[str, float],
                  components: Dict[str, float]) -> str:
        """Log un calcul de score"""
        return self.log_event(
            event_type="SCORE",
            action=score_type,
            description=f"Score '{score_type}' pour '{column}': {score_value:.1%}",
            severity="SUCCESS",
            details={
                "score_type": score_type,
                "column": column,
                "score_value": score_value,
                "score_percent": round(score_value * 100, 2),
                "weights": weights,
                "components": components,
            }
        )

    def log_dama_calculation(self,
                             column: str,
                             dama_scores: Dict[str, float],
                             global_score: float) -> str:
        """Log un calcul DAMA"""
        return self.log_event(
            event_type="DAMA",
            action="dama_calculation",
            description=f"Scores DAMA pour '{column}': {global_score:.1%}",
            severity="SUCCESS",
            details={
                "column": column,
                "dimensions": dama_scores,
                "global_score": global_score,
                "global_percent": round(global_score * 100, 2),
            }
        )

    def log_ahp_weights(self,
                        profile_name: str,
                        weights: Dict[str, float],
                        consistency_ratio: Optional[float] = None) -> str:
        """Log une pondération AHP"""
        return self.log_event(
            event_type="AHP",
            action="weights_calculation",
            description=f"Pondérations AHP pour profil '{profile_name}'",
            severity="SUCCESS",
            details={
                "profile": profile_name,
                "weights": weights,
                "consistency_ratio": consistency_ratio,
            }
        )

    def log_profile_selection(self,
                              profile_name: str,
                              profile_type: str,
                              weights: Dict[str, float]) -> str:
        """Log une sélection de profil"""
        return self.log_event(
            event_type="PROFILE",
            action="profile_selected",
            description=f"Profil '{profile_name}' sélectionné ({profile_type})",
            severity="INFO",
            details={
                "profile_name": profile_name,
                "profile_type": profile_type,
                "weights": weights,
            }
        )

    def log_lineage(self,
                    source_column: str,
                    impact_analysis: Dict[str, Any]) -> str:
        """Log une analyse de lignage"""
        return self.log_event(
            event_type="LINEAGE",
            action="lineage_analysis",
            description=f"Analyse de lignage depuis '{source_column}'",
            severity="SUCCESS",
            details={
                "source_column": source_column,
                "impact_analysis": impact_analysis,
            }
        )

    def log_ai_request(self,
                       request_type: str,
                       prompt_summary: str,
                       tokens_used: int,
                       success: bool,
                       response_summary: Optional[str] = None) -> str:
        """Log une requête IA"""
        return self.log_event(
            event_type="AI_REQUEST",
            action=request_type,
            description=f"Requête IA '{request_type}' ({tokens_used} tokens)",
            severity="SUCCESS" if success else "ERROR",
            details={
                "request_type": request_type,
                "prompt_summary": prompt_summary[:200],  # Limiter
                "tokens_used": tokens_used,
                "success": success,
                "response_summary": response_summary[:200] if response_summary else None,
            }
        )

    def log_report_generation(self,
                              report_type: str,
                              format: str,
                              columns_included: int) -> str:
        """Log une génération de rapport"""
        return self.log_event(
            event_type="REPORT",
            action="report_generated",
            description=f"Rapport '{report_type}' généré en {format}",
            severity="SUCCESS",
            details={
                "report_type": report_type,
                "format": format,
                "columns_included": columns_included,
            }
        )

    def log_export(self,
                   export_type: str,
                   filename: str,
                   format: str,
                   rows: int = 0) -> str:
        """Log un export de données"""
        return self.log_event(
            event_type="FILE_EXPORT",
            action="export",
            description=f"Export {export_type} vers '{filename}'",
            severity="SUCCESS",
            details={
                "export_type": export_type,
                "filename": filename,
                "format": format,
                "rows": rows,
            }
        )

    def log_config_change(self,
                          setting: str,
                          old_value: Any,
                          new_value: Any) -> str:
        """Log un changement de configuration"""
        return self.log_event(
            event_type="CONFIG",
            action="config_changed",
            description=f"Configuration '{setting}' modifiée",
            severity="INFO",
            details={
                "setting": setting,
                "old_value": str(old_value)[:100],
                "new_value": str(new_value)[:100],
            }
        )

    def log_admin_action(self,
                         action: str,
                         description: str,
                         success: bool = True) -> str:
        """Log une action admin"""
        return self.log_event(
            event_type="ADMIN",
            action=action,
            description=description,
            severity="SUCCESS" if success else "ERROR",
            details={"success": success}
        )

    def log_error(self,
                  error_type: str,
                  error_message: str,
                  context: Optional[Dict[str, Any]] = None) -> str:
        """Log une erreur"""
        return self.log_event(
            event_type="ERROR",
            action=error_type,
            description=f"Erreur: {error_message[:100]}",
            severity="ERROR",
            details={
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {},
            }
        )

    # =========================================================================
    # PERSISTANCE
    # =========================================================================

    def _save_to_storage(self):
        """Sauvegarde les événements dans le fichier JSON"""
        try:
            # Charger les événements existants
            existing_events = []
            if self.storage_path.exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    existing_events = data.get("events", [])

            # Fusionner avec les nouveaux (éviter les doublons)
            existing_ids = {e["id"] for e in existing_events}
            new_events = [e for e in self.events if e["id"] not in existing_ids]
            all_events = existing_events + new_events

            # Limiter la taille du fichier (garder les 5000 derniers)
            if len(all_events) > 5000:
                all_events = all_events[-5000:]

            # Sauvegarder
            data = {
                "last_updated": self._get_timestamp(),
                "total_events": len(all_events),
                "events": all_events,
            }

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"Erreur sauvegarde audit trail: {e}")

    def _load_from_storage(self):
        """Charge les événements depuis le fichier JSON"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Charger les événements récents en mémoire
                    all_events = data.get("events", [])
                    self.events = all_events[-self.max_memory_events:]
        except Exception as e:
            print(f"Erreur chargement audit trail: {e}")
            self.events = []

    def _sanitize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Nettoie les résultats pour la sérialisation JSON"""
        sanitized = {}
        for key, value in results.items():
            if isinstance(value, (int, float, str, bool, type(None))):
                sanitized[key] = value
            elif isinstance(value, (list, tuple)):
                sanitized[key] = [str(v)[:100] for v in value[:10]]
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_results(value)
            else:
                sanitized[key] = str(value)[:100]
        return sanitized

    # =========================================================================
    # REQUÊTES ET FILTRES
    # =========================================================================

    def get_events(self,
                   event_type: Optional[str] = None,
                   severity: Optional[str] = None,
                   session_id: Optional[str] = None,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   search_text: Optional[str] = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère les événements avec filtres optionnels.

        Args:
            event_type: Filtrer par type d'événement
            severity: Filtrer par sévérité
            session_id: Filtrer par session
            start_date: Date de début
            end_date: Date de fin
            search_text: Recherche textuelle
            limit: Nombre max de résultats

        Returns:
            Liste des événements filtrés
        """
        # Charger tous les événements du fichier
        all_events = []
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_events = data.get("events", [])
        except Exception:
            all_events = self.events.copy()

        # Appliquer les filtres
        filtered = all_events

        if event_type:
            filtered = [e for e in filtered if e.get("event_type") == event_type]

        if severity:
            filtered = [e for e in filtered if e.get("severity") == severity]

        if session_id:
            filtered = [e for e in filtered if e.get("session_id") == session_id]

        if start_date:
            start_str = start_date.isoformat()
            filtered = [e for e in filtered if e.get("timestamp", "") >= start_str]

        if end_date:
            end_str = end_date.isoformat()
            filtered = [e for e in filtered if e.get("timestamp", "") <= end_str]

        if search_text:
            search_lower = search_text.lower()
            filtered = [
                e for e in filtered
                if search_lower in e.get("description", "").lower()
                or search_lower in e.get("action", "").lower()
                or search_lower in json.dumps(e.get("details", {})).lower()
            ]

        # Trier par date décroissante et limiter
        filtered = sorted(filtered, key=lambda x: x.get("timestamp", ""), reverse=True)
        return filtered[:limit]

    def get_session_events(self) -> List[Dict[str, Any]]:
        """Retourne les événements de la session courante"""
        return self.get_events(session_id=self.session_id, limit=500)

    def get_statistics(self) -> Dict[str, Any]:
        """Retourne des statistiques sur l'audit trail"""
        all_events = self.get_events(limit=10000)

        if not all_events:
            return {"total_events": 0}

        # Compter par type
        type_counts = {}
        for event in all_events:
            etype = event.get("event_type", "UNKNOWN")
            type_counts[etype] = type_counts.get(etype, 0) + 1

        # Compter par sévérité
        severity_counts = {}
        for event in all_events:
            sev = event.get("severity", "INFO")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        # Sessions uniques
        sessions = set(e.get("session_id") for e in all_events)

        return {
            "total_events": len(all_events),
            "events_by_type": type_counts,
            "events_by_severity": severity_counts,
            "unique_sessions": len(sessions),
            "oldest_event": all_events[-1].get("timestamp") if all_events else None,
            "newest_event": all_events[0].get("timestamp") if all_events else None,
        }

    # =========================================================================
    # EXPORTS
    # =========================================================================

    def export_to_dataframe(self,
                            events: Optional[List[Dict[str, Any]]] = None) -> pd.DataFrame:
        """Exporte les événements vers un DataFrame pandas"""
        if events is None:
            events = self.get_events(limit=5000)

        if not events:
            return pd.DataFrame()

        # Aplatir les détails pour l'export
        rows = []
        for event in events:
            row = {
                "ID": event.get("id"),
                "Timestamp": event.get("timestamp"),
                "Session": event.get("session_id"),
                "Type": event.get("event_type_label", event.get("event_type")),
                "Action": event.get("action"),
                "Description": event.get("description"),
                "Sévérité": event.get("severity"),
                "Détails": json.dumps(event.get("details", {}), ensure_ascii=False)[:500],
                "Hash Fichier": event.get("file_hash", ""),
            }
            rows.append(row)

        return pd.DataFrame(rows)

    def export_to_json(self, filepath: str, events: Optional[List[Dict[str, Any]]] = None):
        """Exporte les événements vers un fichier JSON"""
        if events is None:
            events = self.get_events(limit=5000)

        data = {
            "exported_at": self._get_timestamp(),
            "total_events": len(events),
            "events": events,
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def export_to_csv(self, filepath: str, events: Optional[List[Dict[str, Any]]] = None):
        """Exporte les événements vers un fichier CSV"""
        df = self.export_to_dataframe(events)
        df.to_csv(filepath, index=False, encoding='utf-8')

    def clear_old_events(self, days: int = 90):
        """Supprime les événements plus vieux que X jours"""
        cutoff = datetime.now().isoformat()[:10]  # Simplification
        # Note: implémenter si besoin
        pass


# ============================================================================
# INSTANCE GLOBALE
# ============================================================================

_audit_instance: Optional[AuditTrail] = None

def get_audit_trail() -> AuditTrail:
    """Retourne l'instance globale de l'audit trail"""
    global _audit_instance
    if _audit_instance is None:
        _audit_instance = AuditTrail()
    return _audit_instance

def reset_audit_trail():
    """Réinitialise l'instance globale"""
    global _audit_instance
    _audit_instance = None
