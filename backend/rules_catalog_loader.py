"""
Chargeur du catalogue déclaratif rules_catalog.yaml.

Ce module est le point d'entrée unique pour accéder aux définitions
de règles et anomalies. Toute extension (nouveau cas d'usage, nouvelles
anomalies) passe par l'édition du YAML — sans modifier de code Python
tant que le rule_type utilisé existe déjà.

Usage:
    from backend.rules_catalog_loader import catalog

    # Accéder au référentiel (rétrocompatible avec REFERENTIAL)
    ref = catalog.referential
    anomaly = ref["DB#1"]

    # Accéder à la config ODCS d'un rule_type
    odcs_cfg = catalog.get_odcs_config("null_check")

    # Construire une entrée ODCS pour une règle
    entry = catalog.build_odcs_entry(rule_dict, col_name="age", dataset_name="rh")

    # Lister les rule_types disponibles
    types = catalog.rule_types
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any


_CATALOG_PATH = Path(__file__).parent / "rules_catalog.yaml"


class RulesCatalog:
    """Catalogue déclaratif chargé depuis rules_catalog.yaml."""

    def __init__(self, path: Path = _CATALOG_PATH):
        self._path = path
        self._data: Dict = {}
        self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Chargement
    # ──────────────────────────────────────────────────────────────────────

    def _load(self):
        with open(self._path, encoding="utf-8") as f:
            self._data = yaml.safe_load(f) or {}

    def reload(self):
        """Recharge le catalogue (utile en développement)."""
        self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Propriétés
    # ──────────────────────────────────────────────────────────────────────

    @property
    def rule_types(self) -> Dict[str, dict]:
        """Tous les rule_types définis (null_check, range, enum, …)."""
        return self._data.get("rule_types", {})

    @property
    def anomalies(self) -> Dict[str, dict]:
        """Toutes les anomalies (DB#1…UP#40)."""
        return self._data.get("anomalies", {})

    @property
    def referential(self) -> Dict[str, dict]:
        """Alias rétrocompatible → même format que l'ancien REFERENTIAL."""
        return self.anomalies

    @property
    def dimensions(self) -> dict:
        return self._data.get("dimensions", {})

    @property
    def dama_dimensions(self) -> List[str]:
        return self.dimensions.get("dama", [])

    @property
    def causal_dimensions(self) -> dict:
        return self.dimensions.get("causal", {})

    # ──────────────────────────────────────────────────────────────────────
    # Requêtes
    # ──────────────────────────────────────────────────────────────────────

    def get_by_dimension(self, dim: str) -> Dict[str, dict]:
        """Filtre les anomalies par dimension causale (DB, DP, BR, UP)."""
        return {k: v for k, v in self.anomalies.items() if v.get("dimension") == dim}

    def get_auto_detectable(self) -> Dict[str, dict]:
        return {k: v for k, v in self.anomalies.items() if v.get("detection") == "Auto"}

    def get_by_criticality(self, crit: str) -> Dict[str, dict]:
        return {k: v for k, v in self.anomalies.items() if v.get("criticality") == crit}

    def get_by_rule_type(self, rule_type: str) -> Dict[str, dict]:
        """Anomalies qui utilisent un rule_type donné."""
        return {k: v for k, v in self.anomalies.items()
                if v.get("default_rule_type") == rule_type}

    def get_summary(self) -> dict:
        """Statistiques du référentiel — rétrocompatible."""
        by_dim: Dict[str, Dict[str, int]] = {}
        for a in self.anomalies.values():
            dim = a.get("dimension", "?")
            det = a.get("detection", "?")
            by_dim.setdefault(dim, {"total": 0})
            by_dim[dim]["total"] += 1
            by_dim[dim][det] = by_dim[dim].get(det, 0) + 1
        return {"total": len(self.anomalies), "by_dimension": by_dim}

    # ──────────────────────────────────────────────────────────────────────
    # ODCS helpers
    # ──────────────────────────────────────────────────────────────────────

    def get_odcs_config(self, rule_type: str) -> dict:
        """Retourne la config ODCS pour un rule_type."""
        rt_cfg = self.rule_types.get(rule_type, {})
        return rt_cfg.get("odcs", {})

    def get_odcs_metric(self, rule_type: str) -> str:
        """Retourne le metric ODCS (nullValues, duplicateValues, …) ou 'custom'."""
        cfg = self.get_odcs_config(rule_type)
        return cfg.get("metric", "custom")

    def is_library_metric(self, rule_type: str) -> bool:
        """True si le rule_type mappe vers un metric ODCS 'library'."""
        cfg = self.get_odcs_config(rule_type)
        return cfg.get("type") == "library"

    def build_odcs_entry(self, rule: dict, col_name: str = "",
                         dataset_name: str = "dataset") -> dict:
        """Construit une entrée quality ODCS v3.1.0 depuis le catalogue.

        Utilise la config déclarative du rule_type pour le mapping ODCS,
        puis enrichit avec les paramètres spécifiques de la règle.
        """
        rt = rule.get("type", "")
        odcs_cfg = self.get_odcs_config(rt)

        is_library = odcs_cfg.get("type") == "library"
        entry: Dict[str, Any] = {
            "type": "library" if is_library else "custom",
            "description": rule.get("description", ""),
        }

        if is_library and "metric" in odcs_cfg:
            entry["metric"] = odcs_cfg["metric"]

        # ── Threshold from catalog config ──
        op = odcs_cfg.get("threshold_operator")
        unit = odcs_cfg.get("threshold_unit")

        if op == "mustBeLessThan":
            # Valeur depuis la règle (threshold, max_age_days, max_length…)
            # ou depuis le catalog (threshold_value)
            val = self._extract_threshold(rule, odcs_cfg)
            if val is not None:
                entry["mustBeLessThan"] = val
        elif op == "mustBeGreaterThan":
            val = self._extract_threshold_gt(rule, odcs_cfg)
            if val is not None:
                entry["mustBeGreaterThan"] = val
        elif op == "mustBeBetween":
            mn = rule.get("min", 0)
            mx = rule.get("max", 0)
            entry["mustBeBetween"] = [mn, mx]

        if unit:
            entry["unit"] = unit

        # ── SQL query from catalog ──
        query_template = odcs_cfg.get("query", "")
        if query_template and col_name:
            entry["query"] = query_template

        # ── queryParams from rule ──
        query_params = self._build_query_params(rule, rt, col_name)
        if query_params:
            entry["queryParams"] = query_params

        # ── Custom properties (anomaly metadata) ──
        custom = self._build_custom_properties(rule)
        if custom:
            entry["customProperties"] = custom

        return entry

    def _extract_threshold(self, rule: dict, odcs_cfg: dict) -> Optional[float]:
        """Extrait le seuil mustBeLessThan depuis la règle ou le catalog."""
        for key in ("threshold", "max_age_days", "max_length"):
            if key in rule:
                return rule[key]
        rt = rule.get("type", "")
        if rt == "granularity_max":
            return rule.get("max_unique_ratio", 0.9) * 100
        return odcs_cfg.get("threshold_value")

    def _extract_threshold_gt(self, rule: dict, odcs_cfg: dict) -> Optional[float]:
        """Extrait le seuil mustBeGreaterThan."""
        for key in ("min_fill_rate", "min_unique"):
            if key in rule:
                return rule[key]
        return odcs_cfg.get("threshold_value")

    def _build_query_params(self, rule: dict, rt: str, col_name: str) -> dict:
        """Construit les queryParams pour les règles multi-colonnes."""
        params = {}
        if rt == "temporal_order":
            sc = rule.get("start_col", col_name)
            ec = rule.get("end_col", "")
            if ec:
                params = {"start_column": sc, "end_column": ec}
        elif rt == "conditional_required":
            cc = rule.get("condition_col", "")
            cv = rule.get("condition_val", "")
            if cc:
                params = {"condition_column": cc, "condition_value": cv}
        elif rt == "derived_calc":
            sources = rule.get("sources", [])
            formula = rule.get("formula", "")
            if sources:
                params = {"sources": sources, "formula": formula}
        elif rt == "outlier_iqr":
            lo = rule.get("lower", 0)
            hi = rule.get("upper", 0)
            params = {"lower": lo, "upper": hi}
        return params

    def _build_custom_properties(self, rule: dict) -> dict:
        """Construit les customProperties ODCS."""
        custom = {}
        if rule.get("type") == "enum" and rule.get("values"):
            custom["validValues"] = rule["values"]
        if rule.get("anomaly_id"):
            custom["anomalyId"] = rule["anomaly_id"]
        if rule.get("dimension"):
            custom["causalDimension"] = rule["dimension"]
        if rule.get("detection"):
            custom["detectionMethod"] = rule["detection"]
        if rule.get("criticality_ref"):
            custom["criticality"] = rule["criticality_ref"]
        if rule.get("woodall"):
            custom["woodallClass"] = rule["woodall"]
        return custom


# ── Singleton ──────────────────────────────────────────────────────────────
catalog = RulesCatalog()
