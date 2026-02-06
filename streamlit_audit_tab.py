"""
Onglet Historique / Audit Trail pour l'application Streamlit
Affiche et permet de filtrer/exporter l'historique des actions
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import json
import io

# Import du module audit
try:
    from backend.audit_trail import get_audit_trail, AuditTrail
    AUDIT_OK = True
except ImportError:
    AUDIT_OK = False


def render_audit_tab():
    """Rendu de l'onglet Audit Trail / Historique"""

    if not AUDIT_OK:
        st.error("Module audit_trail non disponible")
        return

    audit = get_audit_trail()

    # En-tête
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    ">
        <h3 style="color: white; margin: 0 0 0.5rem 0;">📜 Audit Trail - Historique des Actions</h3>
        <p style="color: rgba(255,255,255,0.8); margin: 0;">
            Traçabilité complète de toutes les opérations effectuées dans l'application.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    stats = audit.get_statistics()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "📊 Total événements",
            f"{stats.get('total_events', 0):,}"
        )

    with col2:
        st.metric(
            "🚀 Sessions uniques",
            stats.get('unique_sessions', 0)
        )

    with col3:
        errors = stats.get('events_by_severity', {}).get('ERROR', 0)
        st.metric(
            "❌ Erreurs",
            errors,
            delta=None if errors == 0 else f"-{errors}" if errors < 5 else None,
            delta_color="inverse"
        )

    with col4:
        st.metric(
            "🔑 Session actuelle",
            audit.session_id
        )

    st.markdown("---")

    # =========================================================================
    # FILTRES
    # =========================================================================

    st.subheader("🔍 Filtres")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Filtre par type
        event_types = ["Tous"] + list(AuditTrail.EVENT_TYPES.keys())
        selected_type = st.selectbox(
            "Type d'événement",
            options=event_types,
            format_func=lambda x: AuditTrail.EVENT_TYPES.get(x, x) if x != "Tous" else "📋 Tous les types"
        )

    with col2:
        # Filtre par sévérité
        severities = ["Tous", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
        selected_severity = st.selectbox(
            "Sévérité",
            options=severities,
            format_func=lambda x: f"{AuditTrail.SEVERITY_LEVELS.get(x, '')} {x}" if x != "Tous" else "📊 Toutes"
        )

    with col3:
        # Filtre par session
        session_filter = st.selectbox(
            "Session",
            options=["Toutes", "Session actuelle"],
            index=1  # Par défaut: session actuelle
        )

    with col4:
        # Recherche textuelle
        search_text = st.text_input(
            "🔎 Recherche",
            placeholder="Rechercher dans les événements..."
        )

    # Période
    col1, col2 = st.columns(2)
    with col1:
        date_range = st.selectbox(
            "Période",
            options=["Dernière heure", "Aujourd'hui", "7 derniers jours", "30 derniers jours", "Tout"],
            index=1
        )

    # Calculer les dates
    now = datetime.now()
    if date_range == "Dernière heure":
        start_date = now - timedelta(hours=1)
    elif date_range == "Aujourd'hui":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_range == "7 derniers jours":
        start_date = now - timedelta(days=7)
    elif date_range == "30 derniers jours":
        start_date = now - timedelta(days=30)
    else:
        start_date = None

    # =========================================================================
    # RÉCUPÉRATION DES ÉVÉNEMENTS
    # =========================================================================

    events = audit.get_events(
        event_type=selected_type if selected_type != "Tous" else None,
        severity=selected_severity if selected_severity != "Tous" else None,
        session_id=audit.session_id if session_filter == "Session actuelle" else None,
        start_date=start_date,
        search_text=search_text if search_text else None,
        limit=500
    )

    st.markdown("---")

    # =========================================================================
    # AFFICHAGE DES ÉVÉNEMENTS
    # =========================================================================

    st.subheader(f"📜 Événements ({len(events)} résultats)")

    if not events:
        st.info("Aucun événement trouvé avec ces filtres")
    else:
        # Vue résumée ou détaillée
        view_mode = st.radio(
            "Mode d'affichage",
            options=["📋 Liste compacte", "📖 Vue détaillée", "📊 Tableau"],
            horizontal=True
        )

        if view_mode == "📋 Liste compacte":
            _render_compact_list(events)
        elif view_mode == "📖 Vue détaillée":
            _render_detailed_view(events)
        else:
            _render_table_view(events, audit)

    st.markdown("---")

    # =========================================================================
    # EXPORTS
    # =========================================================================

    st.subheader("📤 Exports")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Export CSV
        if events:
            df = audit.export_to_dataframe(events)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="📥 Télécharger CSV",
                data=csv_data,
                file_name=f"audit_trail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    with col2:
        # Export JSON
        if events:
            json_data = json.dumps({
                "exported_at": datetime.now().isoformat(),
                "total_events": len(events),
                "events": events
            }, ensure_ascii=False, indent=2)

            st.download_button(
                label="📥 Télécharger JSON",
                data=json_data,
                file_name=f"audit_trail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

    with col3:
        # Statistiques détaillées
        if st.button("📊 Voir statistiques détaillées", use_container_width=True):
            _show_detailed_statistics(audit)


def _render_compact_list(events):
    """Affiche les événements en liste compacte"""
    for event in events[:50]:  # Limiter l'affichage
        timestamp = event.get("timestamp", "")[:19].replace("T", " ")
        severity_icon = event.get("severity_icon", "")
        type_label = event.get("event_type_label", event.get("event_type", ""))
        description = event.get("description", "")

        # Couleur selon sévérité
        severity = event.get("severity", "INFO")
        if severity == "ERROR" or severity == "CRITICAL":
            bg_color = "rgba(235, 51, 73, 0.1)"
            border_color = "#eb3349"
        elif severity == "WARNING":
            bg_color = "rgba(251, 189, 35, 0.1)"
            border_color = "#FBBD23"
        elif severity == "SUCCESS":
            bg_color = "rgba(56, 239, 125, 0.1)"
            border_color = "#38ef7d"
        else:
            bg_color = "rgba(102, 126, 234, 0.05)"
            border_color = "rgba(102, 126, 234, 0.3)"

        st.markdown(f"""
        <div style="
            background: {bg_color};
            border-left: 3px solid {border_color};
            padding: 0.5rem 1rem;
            margin-bottom: 0.5rem;
            border-radius: 0 8px 8px 0;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: rgba(255,255,255,0.6); font-size: 0.8rem;">{timestamp}</span>
                <span style="font-size: 0.75rem; color: rgba(255,255,255,0.5);">{type_label}</span>
            </div>
            <div style="color: white; margin-top: 0.25rem;">
                {severity_icon} {description}
            </div>
        </div>
        """, unsafe_allow_html=True)

    if len(events) > 50:
        st.info(f"Affichage limité à 50 événements. {len(events) - 50} événements supplémentaires disponibles dans l'export.")


def _render_detailed_view(events):
    """Affiche les événements avec tous les détails"""
    for i, event in enumerate(events[:30]):  # Limiter
        with st.expander(
            f"{event.get('severity_icon', '')} {event.get('description', 'Événement')[:60]}",
            expanded=(i == 0)
        ):
            col1, col2 = st.columns([1, 2])

            with col1:
                st.markdown("**Informations**")
                st.text(f"ID: {event.get('id', 'N/A')}")
                st.text(f"Timestamp: {event.get('timestamp', '')[:19]}")
                st.text(f"Session: {event.get('session_id', 'N/A')}")
                st.text(f"Type: {event.get('event_type', 'N/A')}")
                st.text(f"Action: {event.get('action', 'N/A')}")
                st.text(f"Sévérité: {event.get('severity', 'INFO')}")

                if event.get('file_hash'):
                    st.text(f"Hash: {event.get('file_hash')[:16]}...")

            with col2:
                st.markdown("**Détails**")
                details = event.get("details", {})
                if details:
                    st.json(details)
                else:
                    st.text("Aucun détail supplémentaire")

    if len(events) > 30:
        st.info(f"Affichage limité à 30 événements détaillés.")


def _render_table_view(events, audit):
    """Affiche les événements en tableau"""
    df = audit.export_to_dataframe(events)

    if df.empty:
        st.info("Aucun événement à afficher")
        return

    # Reformater pour l'affichage
    df_display = df[["Timestamp", "Type", "Action", "Description", "Sévérité"]].copy()
    df_display["Timestamp"] = df_display["Timestamp"].str[:19].str.replace("T", " ")

    st.dataframe(
        df_display,
        use_container_width=True,
        height=400,
        column_config={
            "Timestamp": st.column_config.TextColumn("⏰ Timestamp", width="medium"),
            "Type": st.column_config.TextColumn("📁 Type", width="medium"),
            "Action": st.column_config.TextColumn("⚡ Action", width="small"),
            "Description": st.column_config.TextColumn("📝 Description", width="large"),
            "Sévérité": st.column_config.TextColumn("🎯 Sévérité", width="small"),
        }
    )


def _show_detailed_statistics(audit):
    """Affiche les statistiques détaillées dans un modal"""
    stats = audit.get_statistics()

    st.markdown("### 📊 Statistiques détaillées")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Événements par type**")
        type_counts = stats.get("events_by_type", {})
        if type_counts:
            for event_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
                label = AuditTrail.EVENT_TYPES.get(event_type, event_type)
                st.text(f"{label}: {count}")

    with col2:
        st.markdown("**Événements par sévérité**")
        sev_counts = stats.get("events_by_severity", {})
        if sev_counts:
            for severity, count in sorted(sev_counts.items(), key=lambda x: -x[1]):
                icon = AuditTrail.SEVERITY_LEVELS.get(severity, "")
                st.text(f"{icon} {severity}: {count}")

    st.markdown("---")
    st.text(f"Premier événement: {stats.get('oldest_event', 'N/A')}")
    st.text(f"Dernier événement: {stats.get('newest_event', 'N/A')}")
