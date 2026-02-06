"""
Data Contracts - Module de gestion des contrats de données
Permet de définir, valider et versionner les attentes qualité sur les datasets
"""

import os
import json
import yaml
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import pandas as pd
import re


class DataContract:
    """
    Représente un contrat de données avec schéma, règles et SLA.

    Un Data Contract définit:
    - Le schéma attendu (colonnes, types, formats)
    - Les règles de qualité (nullabilité, unicité, plages)
    - Les règles métier personnalisées
    - Les SLA (fraîcheur, disponibilité)
    - Les responsabilités (owner, consumers)
    """

    # Types de données supportés
    SUPPORTED_TYPES = [
        "string", "integer", "decimal", "float", "boolean",
        "date", "datetime", "timestamp", "email", "phone",
        "uuid", "url", "json", "array", "any"
    ]

    # Règles de qualité prédéfinies
    BUILTIN_RULES = [
        "not_null", "unique", "not_empty", "no_whitespace_only",
        "in_range", "in_list", "matches_pattern", "min_length", "max_length",
        "is_positive", "is_negative", "is_future", "is_past",
        "is_valid_email", "is_valid_phone", "is_valid_date",
        "no_duplicates", "referential_integrity"
    ]

    def __init__(self, contract_dict: Optional[Dict] = None):
        """Initialise un Data Contract depuis un dictionnaire"""
        self.raw = contract_dict or {}

        # Métadonnées
        self.name = self.raw.get("name", "Untitled Contract")
        self.version = self.raw.get("version", "1.0.0")
        self.description = self.raw.get("description", "")
        self.owner = self.raw.get("owner", "")
        self.created_at = self.raw.get("created_at", datetime.now().isoformat())
        self.updated_at = self.raw.get("updated_at", datetime.now().isoformat())

        # Schéma
        self.schema = self.raw.get("schema", [])

        # Règles de qualité
        self.quality_rules = self.raw.get("quality_rules", [])

        # Règles métier personnalisées
        self.business_rules = self.raw.get("business_rules", [])

        # SLA
        self.sla = self.raw.get("sla", {})

        # Consumers
        self.consumers = self.raw.get("consumers", [])

        # Tags
        self.tags = self.raw.get("tags", [])

    def to_dict(self) -> Dict[str, Any]:
        """Convertit le contract en dictionnaire"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "owner": self.owner,
            "created_at": self.created_at,
            "updated_at": datetime.now().isoformat(),
            "schema": self.schema,
            "quality_rules": self.quality_rules,
            "business_rules": self.business_rules,
            "sla": self.sla,
            "consumers": self.consumers,
            "tags": self.tags,
        }

    def to_yaml(self) -> str:
        """Exporte le contract en YAML"""
        return yaml.dump(self.to_dict(), default_flow_style=False, allow_unicode=True, sort_keys=False)

    def to_json(self) -> str:
        """Exporte le contract en JSON"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> 'DataContract':
        """Charge un contract depuis du YAML"""
        data = yaml.safe_load(yaml_content)
        return cls(data)

    @classmethod
    def from_json(cls, json_content: str) -> 'DataContract':
        """Charge un contract depuis du JSON"""
        data = json.loads(json_content)
        return cls(data)

    @classmethod
    def from_file(cls, filepath: str) -> 'DataContract':
        """Charge un contract depuis un fichier"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if filepath.endswith('.yaml') or filepath.endswith('.yml'):
            return cls.from_yaml(content)
        elif filepath.endswith('.json'):
            return cls.from_json(content)
        else:
            # Essayer YAML d'abord, puis JSON
            try:
                return cls.from_yaml(content)
            except:
                return cls.from_json(content)

    def get_column_spec(self, column_name: str) -> Optional[Dict]:
        """Retourne la spécification d'une colonne"""
        for col in self.schema:
            if col.get("name") == column_name:
                return col
        return None

    def get_hash(self) -> str:
        """Calcule un hash du contract pour détecter les changements"""
        content = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class ContractValidator:
    """
    Valide un DataFrame contre un Data Contract.
    Retourne les violations et le score de conformité.
    """

    def __init__(self, contract: DataContract):
        self.contract = contract
        self.violations: List[Dict] = []
        self.warnings: List[Dict] = []
        self.column_scores: Dict[str, float] = {}

    def validate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Valide un DataFrame contre le contract.

        Returns:
            Dict avec: conformity_score, violations, warnings, column_details
        """
        self.violations = []
        self.warnings = []
        self.column_scores = {}

        # 1. Valider le schéma (colonnes présentes)
        self._validate_schema(df)

        # 2. Valider chaque colonne
        for col_spec in self.contract.schema:
            col_name = col_spec.get("name")
            if col_name in df.columns:
                self._validate_column(df, col_spec)

        # 3. Valider les règles de qualité globales
        for rule in self.contract.quality_rules:
            self._validate_quality_rule(df, rule)

        # 4. Valider les règles métier
        for rule in self.contract.business_rules:
            self._validate_business_rule(df, rule)

        # Calculer le score de conformité global
        total_checks = len(self.violations) + len(self.warnings) + max(1, len(self.contract.schema))
        violations_weight = len(self.violations) * 1.0
        warnings_weight = len(self.warnings) * 0.3
        conformity_score = max(0, 1 - (violations_weight + warnings_weight) / total_checks)

        return {
            "conformity_score": conformity_score,
            "conformity_percent": round(conformity_score * 100, 1),
            "total_violations": len(self.violations),
            "total_warnings": len(self.warnings),
            "violations": self.violations,
            "warnings": self.warnings,
            "column_scores": self.column_scores,
            "contract_name": self.contract.name,
            "contract_version": self.contract.version,
            "validated_at": datetime.now().isoformat(),
        }

    def _validate_schema(self, df: pd.DataFrame):
        """Valide que les colonnes requises sont présentes"""
        df_columns = set(df.columns)

        for col_spec in self.contract.schema:
            col_name = col_spec.get("name")
            required = col_spec.get("required", True)
            nullable = col_spec.get("nullable", True)

            if col_name not in df_columns:
                if required:
                    self.violations.append({
                        "type": "schema",
                        "rule": "column_missing",
                        "column": col_name,
                        "severity": "critical",
                        "message": f"Colonne requise '{col_name}' absente du dataset",
                        "expected": col_name,
                        "actual": "MISSING",
                    })
                else:
                    self.warnings.append({
                        "type": "schema",
                        "rule": "column_missing_optional",
                        "column": col_name,
                        "severity": "low",
                        "message": f"Colonne optionnelle '{col_name}' absente",
                    })

        # Colonnes inattendues
        expected_columns = {col.get("name") for col in self.contract.schema}
        unexpected = df_columns - expected_columns
        if unexpected and self.contract.schema:  # Seulement si le schéma est défini
            for col in unexpected:
                self.warnings.append({
                    "type": "schema",
                    "rule": "unexpected_column",
                    "column": col,
                    "severity": "low",
                    "message": f"Colonne '{col}' non définie dans le contract",
                })

    def _validate_column(self, df: pd.DataFrame, col_spec: Dict):
        """Valide une colonne selon sa spécification"""
        col_name = col_spec.get("name")
        col_data = df[col_name]

        violations_count = 0
        total_checks = 0

        # Type
        expected_type = col_spec.get("type", "any")
        if expected_type != "any":
            total_checks += 1
            type_ok = self._check_type(col_data, expected_type)
            if not type_ok:
                violations_count += 1
                self.violations.append({
                    "type": "type",
                    "rule": "invalid_type",
                    "column": col_name,
                    "severity": "high",
                    "message": f"Type attendu '{expected_type}', type détecté différent",
                    "expected": expected_type,
                })

        # Nullable
        nullable = col_spec.get("nullable", True)
        if not nullable:
            total_checks += 1
            null_count = col_data.isna().sum()
            if null_count > 0:
                violations_count += 1
                self.violations.append({
                    "type": "nullable",
                    "rule": "not_null",
                    "column": col_name,
                    "severity": "high",
                    "message": f"Colonne non nullable contient {null_count} valeurs nulles",
                    "affected_rows": int(null_count),
                    "affected_percent": round(null_count / len(df) * 100, 2),
                })

        # Pattern (regex)
        pattern = col_spec.get("pattern")
        if pattern:
            total_checks += 1
            invalid_count = self._check_pattern(col_data, pattern)
            if invalid_count > 0:
                violations_count += 1
                self.violations.append({
                    "type": "format",
                    "rule": "pattern_mismatch",
                    "column": col_name,
                    "severity": "medium",
                    "message": f"{invalid_count} valeurs ne respectent pas le pattern '{pattern}'",
                    "pattern": pattern,
                    "affected_rows": invalid_count,
                })

        # Format (pour dates)
        date_format = col_spec.get("format")
        if date_format and expected_type in ["date", "datetime"]:
            total_checks += 1
            # Vérification basique du format
            pass

        # Range (min/max)
        value_range = col_spec.get("range")
        if value_range and len(value_range) == 2:
            total_checks += 1
            min_val, max_val = value_range
            out_of_range = self._check_range(col_data, min_val, max_val)
            if out_of_range > 0:
                violations_count += 1
                self.violations.append({
                    "type": "range",
                    "rule": "out_of_range",
                    "column": col_name,
                    "severity": "medium",
                    "message": f"{out_of_range} valeurs hors de la plage [{min_val}, {max_val}]",
                    "range": value_range,
                    "affected_rows": out_of_range,
                })

        # Enum (valeurs autorisées)
        allowed_values = col_spec.get("enum") or col_spec.get("allowed_values")
        if allowed_values:
            total_checks += 1
            invalid_count = self._check_enum(col_data, allowed_values)
            if invalid_count > 0:
                violations_count += 1
                self.violations.append({
                    "type": "enum",
                    "rule": "invalid_value",
                    "column": col_name,
                    "severity": "medium",
                    "message": f"{invalid_count} valeurs non autorisées",
                    "allowed": allowed_values[:10],  # Limiter l'affichage
                    "affected_rows": invalid_count,
                })

        # Min/Max length (pour strings)
        min_length = col_spec.get("min_length")
        max_length = col_spec.get("max_length")
        if min_length is not None or max_length is not None:
            total_checks += 1
            length_violations = self._check_length(col_data, min_length, max_length)
            if length_violations > 0:
                violations_count += 1
                self.violations.append({
                    "type": "length",
                    "rule": "invalid_length",
                    "column": col_name,
                    "severity": "low",
                    "message": f"{length_violations} valeurs avec longueur invalide",
                    "min_length": min_length,
                    "max_length": max_length,
                    "affected_rows": length_violations,
                })

        # Unique
        unique = col_spec.get("unique", False)
        if unique:
            total_checks += 1
            duplicates = col_data.dropna().duplicated().sum()
            if duplicates > 0:
                violations_count += 1
                self.violations.append({
                    "type": "uniqueness",
                    "rule": "duplicates",
                    "column": col_name,
                    "severity": "high",
                    "message": f"{duplicates} valeurs dupliquées (unicité requise)",
                    "affected_rows": int(duplicates),
                })

        # Règles custom de la colonne
        col_rules = col_spec.get("rules", [])
        for rule in col_rules:
            total_checks += 1
            rule_result = self._apply_custom_rule(col_data, rule, df)
            if not rule_result["passed"]:
                violations_count += 1
                self.violations.append({
                    "type": "custom",
                    "rule": rule if isinstance(rule, str) else rule.get("name", "custom"),
                    "column": col_name,
                    "severity": "medium",
                    "message": rule_result.get("message", f"Règle '{rule}' non respectée"),
                    "affected_rows": rule_result.get("affected_rows", 0),
                })

        # Calculer le score de la colonne
        if total_checks > 0:
            self.column_scores[col_name] = 1 - (violations_count / total_checks)
        else:
            self.column_scores[col_name] = 1.0

    def _validate_quality_rule(self, df: pd.DataFrame, rule: Dict):
        """Valide une règle de qualité globale"""
        rule_type = rule.get("rule")
        columns = rule.get("columns", [])
        threshold = rule.get("threshold", 1.0)

        if rule_type == "completeness":
            for col in columns:
                if col in df.columns:
                    completeness = 1 - df[col].isna().mean()
                    if completeness < threshold:
                        self.violations.append({
                            "type": "quality",
                            "rule": "completeness",
                            "column": col,
                            "severity": "high",
                            "message": f"Complétude {completeness:.1%} < seuil {threshold:.1%}",
                            "actual": round(completeness, 4),
                            "threshold": threshold,
                        })

        elif rule_type == "uniqueness":
            if columns:
                if len(columns) == 1:
                    col = columns[0]
                    if col in df.columns:
                        unique_ratio = df[col].nunique() / len(df)
                        if unique_ratio < threshold:
                            self.violations.append({
                                "type": "quality",
                                "rule": "uniqueness",
                                "column": col,
                                "severity": "medium",
                                "message": f"Unicité {unique_ratio:.1%} < seuil {threshold:.1%}",
                                "actual": round(unique_ratio, 4),
                                "threshold": threshold,
                            })
                else:
                    # Unicité composite
                    existing_cols = [c for c in columns if c in df.columns]
                    if existing_cols:
                        duplicates = df.duplicated(subset=existing_cols).sum()
                        if duplicates > 0:
                            self.violations.append({
                                "type": "quality",
                                "rule": "composite_uniqueness",
                                "column": ", ".join(existing_cols),
                                "severity": "high",
                                "message": f"{duplicates} doublons sur clé composite",
                                "affected_rows": int(duplicates),
                            })

    def _validate_business_rule(self, df: pd.DataFrame, rule: Dict):
        """Valide une règle métier personnalisée"""
        rule_name = rule.get("name", "unnamed_rule")
        rule_type = rule.get("type", "custom")
        description = rule.get("description", "")

        # Règle de comparaison entre colonnes
        if rule_type == "comparison":
            col1 = rule.get("column1")
            col2 = rule.get("column2")
            operator = rule.get("operator", ">")

            if col1 in df.columns and col2 in df.columns:
                if operator == ">":
                    violations = (df[col1] <= df[col2]).sum()
                elif operator == ">=":
                    violations = (df[col1] < df[col2]).sum()
                elif operator == "<":
                    violations = (df[col1] >= df[col2]).sum()
                elif operator == "<=":
                    violations = (df[col1] > df[col2]).sum()
                elif operator == "==":
                    violations = (df[col1] != df[col2]).sum()
                else:
                    violations = 0

                if violations > 0:
                    self.violations.append({
                        "type": "business",
                        "rule": rule_name,
                        "column": f"{col1}, {col2}",
                        "severity": rule.get("severity", "medium"),
                        "message": description or f"Règle '{rule_name}' non respectée ({violations} lignes)",
                        "affected_rows": int(violations),
                    })

        # Règle conditionnelle (si A alors B)
        elif rule_type == "conditional":
            condition_col = rule.get("if_column")
            condition_val = rule.get("if_value")
            then_col = rule.get("then_column")
            then_check = rule.get("then_check", "not_null")

            if condition_col in df.columns and then_col in df.columns:
                filtered = df[df[condition_col] == condition_val]
                if then_check == "not_null":
                    violations = filtered[then_col].isna().sum()
                elif then_check == "not_empty":
                    violations = (filtered[then_col].astype(str).str.strip() == "").sum()
                else:
                    violations = 0

                if violations > 0:
                    self.violations.append({
                        "type": "business",
                        "rule": rule_name,
                        "column": then_col,
                        "severity": rule.get("severity", "medium"),
                        "message": description or f"Si {condition_col}={condition_val}, alors {then_col} doit être {then_check}",
                        "affected_rows": int(violations),
                    })

        # Règle d'expression (formule)
        elif rule_type == "expression":
            expression = rule.get("expression")
            # Pour la sécurité, on limite les expressions supportées
            # Implémentation basique
            pass

    def _check_type(self, series: pd.Series, expected_type: str) -> bool:
        """Vérifie le type d'une série"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return True

        if expected_type in ["string", "str"]:
            return non_null.dtype == object
        elif expected_type in ["integer", "int"]:
            try:
                return pd.api.types.is_integer_dtype(non_null) or non_null.apply(lambda x: float(x).is_integer()).all()
            except:
                return False
        elif expected_type in ["decimal", "float", "number"]:
            return pd.api.types.is_numeric_dtype(non_null)
        elif expected_type == "boolean":
            return non_null.dtype == bool or set(non_null.unique()).issubset({True, False, 0, 1, "true", "false"})
        elif expected_type in ["date", "datetime"]:
            try:
                pd.to_datetime(non_null)
                return True
            except:
                return False
        elif expected_type == "email":
            pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            return non_null.astype(str).str.match(pattern).all()

        return True

    def _check_pattern(self, series: pd.Series, pattern: str) -> int:
        """Compte les valeurs ne respectant pas le pattern"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return 0
        try:
            matches = non_null.astype(str).str.match(pattern)
            return (~matches).sum()
        except:
            return 0

    def _check_range(self, series: pd.Series, min_val, max_val) -> int:
        """Compte les valeurs hors plage"""
        try:
            numeric = pd.to_numeric(series, errors='coerce')
            out = ((numeric < min_val) | (numeric > max_val)).sum()
            return int(out)
        except:
            return 0

    def _check_enum(self, series: pd.Series, allowed: List) -> int:
        """Compte les valeurs non autorisées"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return 0
        return (~non_null.isin(allowed)).sum()

    def _check_length(self, series: pd.Series, min_len: Optional[int], max_len: Optional[int]) -> int:
        """Compte les valeurs avec longueur invalide"""
        non_null = series.dropna().astype(str)
        if len(non_null) == 0:
            return 0

        lengths = non_null.str.len()
        violations = 0
        if min_len is not None:
            violations += (lengths < min_len).sum()
        if max_len is not None:
            violations += (lengths > max_len).sum()
        return int(violations)

    def _apply_custom_rule(self, series: pd.Series, rule: Union[str, Dict], df: pd.DataFrame) -> Dict:
        """Applique une règle custom"""
        if isinstance(rule, str):
            rule_name = rule
            rule_params = {}
        else:
            rule_name = rule.get("name", "")
            rule_params = rule

        # Règles prédéfinies
        if rule_name == "must_be_past":
            try:
                dates = pd.to_datetime(series, errors='coerce')
                future = (dates > datetime.now()).sum()
                return {"passed": future == 0, "affected_rows": int(future), "message": f"{future} dates futures"}
            except:
                return {"passed": True, "affected_rows": 0}

        elif rule_name == "must_be_future":
            try:
                dates = pd.to_datetime(series, errors='coerce')
                past = (dates < datetime.now()).sum()
                return {"passed": past == 0, "affected_rows": int(past), "message": f"{past} dates passées"}
            except:
                return {"passed": True, "affected_rows": 0}

        elif rule_name.startswith("must_be_after:"):
            try:
                threshold_date = pd.to_datetime(rule_name.split(":")[1].strip())
                dates = pd.to_datetime(series, errors='coerce')
                before = (dates < threshold_date).sum()
                return {"passed": before == 0, "affected_rows": int(before)}
            except:
                return {"passed": True, "affected_rows": 0}

        elif rule_name == "is_positive":
            try:
                numeric = pd.to_numeric(series, errors='coerce')
                negative = (numeric < 0).sum()
                return {"passed": negative == 0, "affected_rows": int(negative)}
            except:
                return {"passed": True, "affected_rows": 0}

        return {"passed": True, "affected_rows": 0}


class ContractRepository:
    """
    Gestionnaire de repository de Data Contracts.
    Gère le versioning et la persistance.
    """

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            project_dir = Path(__file__).parent.parent
            self.storage_path = project_dir / ".contracts"

        self.storage_path.mkdir(exist_ok=True)
        self.index_file = self.storage_path / "index.json"
        self._load_index()

    def _load_index(self):
        """Charge l'index des contracts"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                self.index = json.load(f)
        else:
            self.index = {"contracts": {}}

    def _save_index(self):
        """Sauvegarde l'index"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)

    def save_contract(self, contract: DataContract) -> str:
        """
        Sauvegarde un contract avec versioning.

        Returns:
            Contract ID
        """
        contract_id = contract.name.lower().replace(" ", "_")
        version = contract.version

        # Créer le dossier du contract
        contract_dir = self.storage_path / contract_id
        contract_dir.mkdir(exist_ok=True)

        # Sauvegarder la version
        filename = f"v{version.replace('.', '_')}.yaml"
        filepath = contract_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(contract.to_yaml())

        # Mettre à jour l'index
        if contract_id not in self.index["contracts"]:
            self.index["contracts"][contract_id] = {
                "name": contract.name,
                "versions": [],
                "latest": version,
                "created_at": datetime.now().isoformat(),
            }

        if version not in self.index["contracts"][contract_id]["versions"]:
            self.index["contracts"][contract_id]["versions"].append(version)

        self.index["contracts"][contract_id]["latest"] = version
        self.index["contracts"][contract_id]["updated_at"] = datetime.now().isoformat()

        self._save_index()

        return contract_id

    def get_contract(self, contract_id: str, version: Optional[str] = None) -> Optional[DataContract]:
        """Récupère un contract (dernière version par défaut)"""
        if contract_id not in self.index["contracts"]:
            return None

        if version is None:
            version = self.index["contracts"][contract_id]["latest"]

        filename = f"v{version.replace('.', '_')}.yaml"
        filepath = self.storage_path / contract_id / filename

        if filepath.exists():
            return DataContract.from_file(str(filepath))
        return None

    def list_contracts(self) -> List[Dict]:
        """Liste tous les contracts"""
        result = []
        for contract_id, info in self.index["contracts"].items():
            result.append({
                "id": contract_id,
                "name": info["name"],
                "latest_version": info["latest"],
                "versions": info["versions"],
                "updated_at": info.get("updated_at"),
            })
        return result

    def get_versions(self, contract_id: str) -> List[str]:
        """Liste les versions d'un contract"""
        if contract_id in self.index["contracts"]:
            return self.index["contracts"][contract_id]["versions"]
        return []

    def delete_contract(self, contract_id: str, version: Optional[str] = None):
        """Supprime un contract ou une version"""
        if contract_id not in self.index["contracts"]:
            return

        contract_dir = self.storage_path / contract_id

        if version:
            # Supprimer une version spécifique
            filename = f"v{version.replace('.', '_')}.yaml"
            filepath = contract_dir / filename
            if filepath.exists():
                filepath.unlink()
            self.index["contracts"][contract_id]["versions"].remove(version)
        else:
            # Supprimer tout le contract
            import shutil
            if contract_dir.exists():
                shutil.rmtree(contract_dir)
            del self.index["contracts"][contract_id]

        self._save_index()


def create_template_contract() -> DataContract:
    """Crée un template de Data Contract à personnaliser"""
    template = {
        "name": "Mon Dataset",
        "version": "1.0.0",
        "description": "Description du dataset et de son usage",
        "owner": "equipe@exemple.com",

        "schema": [
            {
                "name": "ID",
                "type": "string",
                "description": "Identifiant unique",
                "nullable": False,
                "unique": True,
                "pattern": "^[A-Z]{3}[0-9]{6}$",
            },
            {
                "name": "Nom",
                "type": "string",
                "description": "Nom complet",
                "nullable": False,
                "min_length": 2,
                "max_length": 100,
            },
            {
                "name": "Email",
                "type": "email",
                "description": "Adresse email",
                "nullable": True,
            },
            {
                "name": "Date_Creation",
                "type": "date",
                "description": "Date de création",
                "format": "YYYY-MM-DD",
                "nullable": False,
                "rules": ["must_be_past"],
            },
            {
                "name": "Montant",
                "type": "decimal",
                "description": "Montant en euros",
                "nullable": True,
                "range": [0, 1000000],
            },
            {
                "name": "Statut",
                "type": "string",
                "description": "Statut actuel",
                "enum": ["Actif", "Inactif", "En attente"],
            },
        ],

        "quality_rules": [
            {
                "rule": "completeness",
                "description": "Complétude minimale requise",
                "columns": ["ID", "Nom"],
                "threshold": 0.99,
            },
            {
                "rule": "uniqueness",
                "description": "Unicité de l'identifiant",
                "columns": ["ID"],
            },
        ],

        "business_rules": [
            {
                "name": "date_coherente",
                "type": "comparison",
                "description": "La date de création doit être dans le passé",
                "severity": "high",
            },
            {
                "name": "montant_si_actif",
                "type": "conditional",
                "description": "Si Statut=Actif, Montant doit être renseigné",
                "if_column": "Statut",
                "if_value": "Actif",
                "then_column": "Montant",
                "then_check": "not_null",
                "severity": "medium",
            },
        ],

        "sla": {
            "freshness": "24h",
            "availability": "99.9%",
            "quality_score_min": 0.95,
        },

        "consumers": [
            {"name": "Application Paie", "contact": "paie@exemple.com"},
            {"name": "Dashboard RH", "contact": "rh@exemple.com"},
        ],

        "tags": ["RH", "SIRH", "Production"],
    }

    return DataContract(template)


def get_template_yaml() -> str:
    """Retourne le template YAML à télécharger"""
    return create_template_contract().to_yaml()
