"""Página de inicio — métricas y últimas solicitudes."""

from datetime import date, datetime
import streamlit as st
import core.queries as q
from core.styles import metric_card, badge_semaforo


def render():
    st.title("Inicio")

    solicitudes = q.get_solicitudes()

    # ── Métricas ──────────────────────────────────────────────
    total      = len(solicitudes)
    en_proceso = sum(1 for s in solicitudes if s["estado"] in ("borrador", "solicitada", "planificada", "en_ejecucion"))
    completadas = sum(1 for s in solicitudes if s["estado"] == "completada")

    # Atrasadas: solicitudes con algún trabajo activo con fecha_entrega vencida
    hoy = date.today()

    def tiene_atraso(sol):
        trabajos = sol.get("ot_trabajos") or []
        for t in trabajos:
            if t.get("estado") in ("completado", "cancelado"):
                continue
            fe = t.get("fecha_entrega")
            if fe:
                if isinstance(fe, str):
                    from datetime import datetime
                    fe = datetime.strptime(fe, "%Y-%m-%d").date()
                if fe < hoy:
                    return True
        return False

    atrasadas = sum(1 for s in solicitudes if tiene_atraso(s))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(metric_card(total, "Total Solicitudes"), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card(en_proceso, "En Proceso"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card(completadas, "Completadas"), unsafe_allow_html=True)
    with c4:
        st.markdown(metric_card(atrasadas, "⚠️ Atrasadas"), unsafe_allow_html=True)

    st.divider()

    # ── Últimas solicitudes ────────────────────────────────────
    st.subheader("Últimas solicitudes")

    _BADGE_SOL = {
        "borrador":     ("badge-gris",    "📝 Borrador"),
        "solicitada":   ("badge-amarillo","📨 Solicitada"),
        "planificada":  ("badge-amarillo","📋 Planificada"),
        "en_ejecucion": ("badge-amarillo","⚙️ En ejecución"),
        "completada":   ("badge-verde",   "✅ Completada"),
        "cancelada":    ("badge-gris",    "❌ Cancelada"),
    }

    recientes = solicitudes[:20]
    if not recientes:
        st.info("No hay solicitudes aún. Crea la primera desde '📝 Nueva Solicitud'.")
        return

    for sol in recientes:
        cls, lbl = _BADGE_SOL.get(sol["estado"], ("badge-gris", sol["estado"]))
        trabajos = sol.get("ot_trabajos") or []
        n_trab = len(trabajos)
        n_comp = sum(1 for t in trabajos if t.get("estado") == "completado")
        created = sol.get("created_at", "")[:10]

        col_num, col_est, col_trab, col_fecha = st.columns([2, 2, 2, 2])
        with col_num:
            st.markdown(f"**{sol['numero']}**")
        with col_est:
            st.markdown(f'<span class="badge {cls}">{lbl}</span>', unsafe_allow_html=True)
        with col_trab:
            st.caption(f"{n_comp}/{n_trab} trabajos completados")
        with col_fecha:
            st.caption(f"Creada: {created}")
        st.markdown("<hr style='margin:4px 0;border-color:#eee;'>", unsafe_allow_html=True)
