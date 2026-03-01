"""
streamlit_anomaly_detection.py
Interface Streamlit complète pour détection anomalies

Features:
- Scan dataset avec détections réelles
- Gestion référentiel (voir, ajouter anomalies)
- Stats apprentissage temps réel
- Historique scans
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from extended_anomaly_catalog import ExtendedCatalogManager, CoreAnomaly, Dimension, Criticality
from adaptive_scan_engine import AdaptiveScanEngine
from rules_catalog_loader import catalog as _catalog


def render_anomaly_detection_tab():
    """Onglet complet détection anomalies"""
    
    st.header("🔍 Détection Anomalies Adaptative")
    
    # Initialiser engine en session state
    if 'adaptive_engine' not in st.session_state:
        st.session_state.adaptive_engine = AdaptiveScanEngine()
    
    engine = st.session_state.adaptive_engine
    
    # Tabs internes
    sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
        "🚀 Scanner Dataset",
        "📚 Référentiel",
        "📈 Apprentissage",
        "📜 Historique"
    ])
    
    # ========================================================================
    # TAB 1 : SCANNER DATASET
    # ========================================================================
    
    with sub_tab1:
        st.subheader("Scanner Dataset")
        
        st.info(f"""
        ✅ **15 détecteurs réels** opérationnels ({len(engine.catalog_manager.catalog)} catalogués)
        🧠 **Apprentissage adaptatif** : Le moteur s'améliore à chaque scan
        ⚡ **3 budgets** : QUICK (top 5) | STANDARD (top 10) | DEEP (tous)
        """)
        
        # Vérifier si dataset déjà chargé dans session_state
        if 'df' in st.session_state and st.session_state.df is not None:
            df = st.session_state.df
            
            st.success(f"✅ Dataset chargé : {len(df):,} lignes × {len(df.columns)} colonnes")
            
            # Aperçu données
            with st.expander("👁️ Aperçu données"):
                st.dataframe(df.head(10), use_container_width=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Lignes", f"{len(df):,}")
                with col2:
                    st.metric("Colonnes", len(df.columns))
                with col3:
                    st.metric("Taille mémoire", f"{df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
            
            # Configuration scan
            st.markdown("---")
            st.subheader("⚙️ Configuration Scan")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                budget = st.selectbox(
                    "Budget",
                    options=["QUICK", "STANDARD", "DEEP"],
                    index=1,
                    help="QUICK=Top 5 | STANDARD=Top 10 | DEEP=Tous"
                )
            
            with col2:
                learn = st.checkbox(
                    "Activer apprentissage",
                    value=True,
                    help="Mettre à jour stats fréquence après scan"
                )
            
            with col3:
                # Utiliser nom de session_state ou défaut
                default_name = st.session_state.get('dataset_name', 'dataset')
                dataset_name = st.text_input(
                    "Nom dataset",
                    value=default_name,
                    help="Nom pour identifier ce scan"
                )
            
            # Lancer scan
            if st.button("🚀 Lancer Scan", type="primary", use_container_width=True):
                try:
                    with st.spinner("🔍 Scan en cours..."):
                        report = engine.scan_dataset(
                            df,
                            dataset_name,
                            budget=budget,
                            learn=learn,
                            verbose=False
                        )
                    
                    # Résultats
                    st.success(f"✅ Scan terminé en {report.total_execution_time_s:.2f}s")
                    
                    # Métriques principales
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Anomalies scannées",
                            report.anomalies_scanned,
                            help="Nombre d'anomalies vérifiées"
                        )
                    
                    with col2:
                        st.metric(
                            "Détections",
                            report.anomalies_detected,
                            delta=f"{report.anomalies_detected/report.anomalies_scanned:.0%}" if report.anomalies_scanned > 0 else "0%",
                            delta_color="inverse"
                        )
                    
                    with col3:
                        st.metric(
                            "Lignes affectées",
                            sum(r.affected_rows for r in report.results if r.detected),
                            help="Total lignes avec anomalies"
                        )
                    
                    with col4:
                        st.metric(
                            "Temps moyen/anomalie",
                            f"{report.total_execution_time_s*1000/report.anomalies_scanned:.1f}ms" if report.anomalies_scanned > 0 else "0ms"
                        )
                    
                    # Graphique répartition
                    st.markdown("---")
                    st.subheader("📊 Répartition Détections")
                    
                    detected_by_dim = report._get_detected_by_dim()
                    
                    if detected_by_dim:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig = px.pie(
                                values=list(detected_by_dim.values()),
                                names=list(detected_by_dim.keys()),
                                title="Détections par Dimension"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            # Timeline exécution
                            timeline_data = []
                            for r in report.results:
                                timeline_data.append({
                                    'Anomalie': r.anomaly_id,
                                    'Temps (ms)': r.execution_time_ms,
                                    'Détecté': '✅ Oui' if r.detected else '⚪ Non'
                                })
                            
                            timeline_df = pd.DataFrame(timeline_data)
                            fig = px.bar(
                                timeline_df,
                                x='Anomalie',
                                y='Temps (ms)',
                                color='Détecté',
                                title="Temps d'exécution par anomalie"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("ℹ️ Aucune anomalie détectée")
                    
                    # Tableau détaillé anomalies
                    st.markdown("---")
                    st.subheader("📋 Détails Anomalies")
                    
                    tab_all, tab_detected, tab_clean = st.tabs([
                        f"Toutes ({len(report.results)})",
                        f"Détectées ({report.anomalies_detected})",
                        f"Clean ({len(report.results) - report.anomalies_detected})"
                    ])
                    
                    with tab_all:
                        all_data = []
                        for r in report.results:
                            all_data.append({
                                'ID': r.anomaly_id,
                                'Anomalie': r.anomaly_name,
                                'Statut': '✅ Détectée' if r.detected else '⚪ OK',
                                'Lignes affectées': r.affected_rows if r.detected else 0,
                                'Temps (ms)': f"{r.execution_time_ms:.1f}"
                            })
                        st.dataframe(pd.DataFrame(all_data), use_container_width=True, hide_index=True)
                    
                    with tab_detected:
                        detected_data = []
                        for r in report.results:
                            if r.detected:
                                detected_data.append({
                                    'ID': r.anomaly_id,
                                    'Anomalie': r.anomaly_name,
                                    'Lignes affectées': r.affected_rows,
                                    'Échantillon': len(r.sample_data)
                                })
                        
                        if detected_data:
                            st.dataframe(pd.DataFrame(detected_data), use_container_width=True, hide_index=True)
                            
                            # Afficher échantillons
                            st.markdown("**📌 Échantillons lignes affectées**")
                            for r in report.results:
                                if r.detected and r.sample_data:
                                    with st.expander(f"{r.anomaly_id}: {r.anomaly_name} ({r.affected_rows} lignes)"):
                                        sample_df = pd.DataFrame(r.sample_data)
                                        st.dataframe(sample_df, use_container_width=True)
                                        
                                        # Détails techniques
                                        if r.details:
                                            st.json(r.details)
                        else:
                            st.success("✅ Aucune anomalie détectée - Dataset clean !")
                    
                    with tab_clean:
                        clean_data = []
                        for r in report.results:
                            if not r.detected:
                                clean_data.append({
                                    'ID': r.anomaly_id,
                                    'Anomalie': r.anomaly_name,
                                    'Temps (ms)': f"{r.execution_time_ms:.1f}"
                                })
                        st.dataframe(pd.DataFrame(clean_data), use_container_width=True, hide_index=True)
                
                except Exception as e:
                    st.error(f"❌ Erreur scan dataset : {e}")
        
        else:
            st.warning("⚠️ Aucun dataset chargé. Veuillez d'abord charger un dataset dans la barre latérale.")
            st.info("👈 Utilisez la barre latérale pour charger un fichier CSV/Excel")
    
    # ========================================================================
    # TAB 2 : RÉFÉRENTIEL
    # ========================================================================
    
    with sub_tab2:
        st.subheader("📚 Référentiel Anomalies")
        
        catalog_manager = engine.catalog_manager
        
        # Stats catalogue
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Anomalies", len(catalog_manager.catalog))
        
        with col2:
            db_count = len(catalog_manager.get_by_dimension('DB'))
            st.metric("DB", db_count)
        
        with col3:
            dp_count = len(catalog_manager.get_by_dimension('DP'))
            st.metric("DP", dp_count)
        
        with col4:
            br_count = len(catalog_manager.get_by_dimension('BR'))
            st.metric("BR", br_count)
        
        with col5:
            up_count = len(catalog_manager.get_by_dimension('UP'))
            st.metric("UP", up_count)
        
        # Visualisation catalogue
        st.markdown("---")
        st.markdown("#### 📊 Vue Catalogue")
        
        catalog_data = []
        for a in catalog_manager.catalog:
            catalog_data.append({
                'ID': a.id,
                'Nom': a.name,
                'Dimension': a.dimension.value,
                'Criticité': a.criticality.name,
                'Woodall': a.woodall_level,
                'Scans': a.scan_count,
                'Détections': a.detection_count,
                'Fréquence': f"{a.frequency:.1%}" if a.scan_count > 0 else "N/A",
                'Score Priorité': f"{a.get_priority_score():.1f}"
            })
        
        catalog_df = pd.DataFrame(catalog_data)
        
        # Filtres
        col1, col2 = st.columns(2)
        
        with col1:
            filter_dim = st.multiselect(
                "Filtrer par dimension",
                options=['DB', 'DP', 'BR', 'UP'],
                default=['DB', 'DP', 'BR', 'UP']
            )
        
        with col2:
            filter_crit = st.multiselect(
                "Filtrer par criticité",
                options=['CRITIQUE', 'ÉLEVÉ', 'MOYEN', 'FAIBLE'],
                default=['CRITIQUE', 'ÉLEVÉ', 'MOYEN', 'FAIBLE']
            )
        
        # Appliquer filtres
        filtered_df = catalog_df[
            catalog_df['Dimension'].isin(filter_dim) &
            catalog_df['Criticité'].isin(filter_crit)
        ]
        
        st.dataframe(
            filtered_df.sort_values('Score Priorité', ascending=False),
            use_container_width=True,
            hide_index=True
        )
        
        # Détails anomalie
        st.markdown("---")
        st.markdown("#### 🔍 Détails Anomalie")
        
        selected_id = st.selectbox(
            "Sélectionner anomalie",
            options=[a.id for a in catalog_manager.catalog],
            format_func=lambda x: f"{x}: {catalog_manager.get_by_id(x).name}"
        )
        
        if selected_id:
            anomaly = catalog_manager.get_by_id(selected_id)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Nom** : {anomaly.name}")
                st.markdown(f"**Description** : {anomaly.description}")
                st.markdown(f"**Dimension** : {anomaly.dimension.value}")
                st.markdown(f"**Criticité** : {anomaly.criticality.name}")
            
            with col2:
                st.markdown(f"**Woodall** : {anomaly.woodall_level}")
                st.markdown(f"**SQL Template** :")
                st.code(anomaly.sql_template, language='sql')
            
            st.markdown(f"**Exemple** : {anomaly.example}")
            
            # Stats apprentissage
            if anomaly.scan_count > 0:
                st.markdown("**📈 Stats Apprentissage** :")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Scans", anomaly.scan_count)
                with col2:
                    st.metric("Détections", anomaly.detection_count)
                with col3:
                    st.metric("Fréquence", f"{anomaly.frequency:.1%}")
                with col4:
                    st.metric("Score Priorité", f"{anomaly.get_priority_score():.1f}")
        
        # Ajouter anomalies par CSV
        st.markdown("---")
        st.markdown("#### ➕ Ajouter Anomalies (import CSV)")

        with st.expander("Importer un CSV d'anomalies"):
            st.markdown("""
            **Colonnes obligatoires** : `anomaly_id`, `name`, `description`, `dimension`, `detection`, `criticality`
            **Colonnes optionnelles** : `woodall`, `algorithm`, `business_risk`, `frequency`, `default_rule_type`
            """)

            csv_template = _catalog.generate_csv_template()
            st.download_button(
                label="📄 Télécharger le template CSV",
                data=csv_template,
                file_name="anomalies_template.csv",
                mime="text/csv",
                key="scan_csv_template",
            )

            csv_file = st.file_uploader(
                "📁 Charger un CSV d'anomalies",
                type=["csv"],
                key="scan_anomaly_csv_upload",
            )

            if csv_file is not None:
                try:
                    import_df = pd.read_csv(csv_file, dtype=str).fillna("")
                    st.markdown(f"**Aperçu** — {len(import_df)} anomalies trouvées :")
                    st.dataframe(import_df, use_container_width=True, hide_index=True)

                    errors = _catalog.validate_import_df(import_df)
                    if errors:
                        for err in errors:
                            st.error(f"❌ {err}")
                    else:
                        existing = set(_catalog.anomalies.keys())
                        new_ids = set(import_df["anomaly_id"].str.strip()) - existing
                        update_ids = set(import_df["anomaly_id"].str.strip()) & existing

                        if new_ids:
                            st.info(f"🆕 {len(new_ids)} nouvelles anomalies : {', '.join(sorted(new_ids))}")
                        if update_ids:
                            st.warning(f"♻️ {len(update_ids)} anomalies déjà existantes : {', '.join(sorted(update_ids))}")

                        col_a, col_b = st.columns(2)
                        with col_a:
                            overwrite = st.checkbox("Écraser les anomalies existantes", value=False, key="scan_overwrite")
                        with col_b:
                            if st.button("✅ Importer dans le catalogue", type="primary", key="scan_import_btn"):
                                result = _catalog.import_from_dataframe(import_df, overwrite=overwrite)
                                if result["errors"]:
                                    for err in result["errors"]:
                                        st.error(f"❌ {err}")
                                else:
                                    msg_parts = []
                                    if result["added"] > 0:
                                        msg_parts.append(f"🆕 {result['added']} ajoutées")
                                    if result["updated"] > 0:
                                        msg_parts.append(f"♻️ {result['updated']} mises à jour")
                                    if result["skipped"] > 0:
                                        msg_parts.append(f"⏭️ {result['skipped']} ignorées (déjà existantes)")
                                    st.success(f"✅ Import réussi — {' · '.join(msg_parts)}")
                                    st.info(f"📊 Le référentiel contient maintenant **{len(_catalog.anomalies)} anomalies**")
                                    # Recharger le catalogue dans le moteur
                                    engine.catalog_manager = ExtendedCatalogManager()
                                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Erreur de lecture CSV : {e}")
    
    # ========================================================================
    # TAB 3 : APPRENTISSAGE
    # ========================================================================
    
    with sub_tab3:
        st.subheader("📈 Apprentissage Adaptatif")
        
        st.info("""
        🧠 Le moteur **apprend** des scans passés pour **optimiser** les suivants :
        - Fréquence : Quelles anomalies sont souvent détectées ?
        - Priorisation : Score = Fréquence × Impact / Complexité
        - Adaptation : Budget QUICK cible les top anomalies
        """)
        
        # Stats apprentissage
        stats_df = engine.get_learning_stats()
        
        if not stats_df.empty:
            st.success(f"✅ {len(stats_df)} anomalies avec historique")
            
            # Métriques globales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_scans = stats_df['Scans'].astype(int).sum()
                st.metric("Total Scans", total_scans)
            
            with col2:
                total_detections = stats_df['Détections'].astype(int).sum()
                st.metric("Total Détections", total_detections)
            
            with col3:
                # Filtrer les N/A avant conversion
                freq_series = stats_df['Fréquence'].str.rstrip('%')
                freq_series = pd.to_numeric(freq_series, errors='coerce')
                avg_freq = freq_series.mean() / 100 if not freq_series.isna().all() else 0
                st.metric("Fréquence moyenne", f"{avg_freq:.1%}")
            
            with col4:
                avg_score = stats_df['_score_numeric'].mean()
                st.metric("Score moyen", f"{avg_score:.1f}")
            
            # Tableau stats
            st.markdown("---")
            st.markdown("#### 📊 Statistiques par Anomalie")
            
            # Afficher sans la colonne cachée
            display_df = stats_df.drop(columns=['_score_numeric'])
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Graphiques
            st.markdown("---")
            st.markdown("#### 📈 Visualisations")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Top 10 fréquences
                top_freq = stats_df.nlargest(10, '_score_numeric')
                fig = px.bar(
                    top_freq,
                    x='ID',
                    y='_score_numeric',
                    color='Dimension',
                    title="Top 10 Score Priorité",
                    labels={'_score_numeric': 'Score Priorité'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Répartition fréquences par dimension
                def safe_freq_mean(x):
                    """Calcule moyenne fréquence en gérant N/A"""
                    cleaned = x.str.rstrip('%')
                    numeric = pd.to_numeric(cleaned, errors='coerce')
                    return numeric.mean() if not numeric.isna().all() else 0
                
                freq_by_dim = stats_df.groupby('Dimension')['Fréquence'].apply(safe_freq_mean).reset_index()
                freq_by_dim.columns = ['Dimension', 'Fréquence Moyenne']
                
                fig = px.pie(
                    freq_by_dim,
                    values='Fréquence Moyenne',
                    names='Dimension',
                    title="Fréquence Moyenne par Dimension"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Export stats
            st.markdown("---")
            if st.button("📥 Télécharger Stats CSV"):
                csv = stats_df.to_csv(index=False)
                st.download_button(
                    label="⬇️ stats_apprentissage.csv",
                    data=csv,
                    file_name=f"stats_apprentissage_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
        
        else:
            st.info("ℹ️ Aucun historique - Lancez un premier scan pour commencer l'apprentissage")
    
    # ========================================================================
    # TAB 4 : HISTORIQUE
    # ========================================================================
    
    with sub_tab4:
        st.subheader("📜 Historique Scans")
        
        history_df = engine.get_scan_history_summary()
        
        if not history_df.empty:
            st.success(f"✅ {len(history_df)} scans dans l'historique")
            
            # Tableau historique
            st.dataframe(history_df, use_container_width=True, hide_index=True)
            
            # Évolution détections
            st.markdown("---")
            st.markdown("#### 📈 Évolution Détections")
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=history_df['Date'],
                y=history_df['Détectées'].astype(int),
                mode='lines+markers',
                name='Détections',
                line=dict(color='red', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=history_df['Date'],
                y=history_df['Scannées'].astype(int),
                mode='lines+markers',
                name='Scannées',
                line=dict(color='blue', width=2, dash='dash')
            ))
            
            fig.update_layout(
                title="Évolution Détections vs Scannées",
                xaxis_title="Date",
                yaxis_title="Nombre Anomalies",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("ℹ️ Aucun scan dans l'historique")


# ============================================================================
# INTÉGRATION DANS APP.PY
# ============================================================================

"""
Pour intégrer dans app.py :

1. Ajouter import en haut :
   from streamlit_anomaly_detection import render_anomaly_detection_tab

2. Ajouter onglet dans st.tabs() :
   tab1, tab2, ..., tab_new = st.tabs([
       "📊 Dashboard",
       ...
       "🔍 Détection Anomalies"
   ])
   
   with tab_new:
       render_anomaly_detection_tab()
"""
