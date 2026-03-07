"""Página Seguimiento Tareas — planilla con todas las tareas activas."""

import datetime
import pandas as pd
import streamlit as st
import core.queries as q
from core.config import LABEL_ESTADO_TRAB


def _fecha_d(val):
    if not val:
        return None
    if isinstance(val, str):
        return datetime.date.fromisoformat(val)
    return val


def render():


    solicitudes = q.get_solicitudes()
    activas     = [s for s in solicitudes if s["estado"] not in ("borrador", "cancelada")]

    if not activas:
        st.info("No hay tareas en seguimiento.")
        return

    filas = []
    correlativo = 1
    for sol in activas:
        trabajos = q.get_trabajos(sol["id"])
        for t in trabajos:
            if t["estado"] == "cancelado":
                continue
            filas.append({
                "☑":            False,
                "N°":           correlativo,
                "N° Solicitud": sol["numero"],
                "Tarea":        t["descripcion"],

                "Estado":       LABEL_ESTADO_TRAB.get(t["estado"], t["estado"]),
                "Ubicación":    t.get("ubicacion") or "—",
            })
            correlativo += 1

    if not filas:
        st.info("No hay tareas en seguimiento.")
        return

    df = pd.DataFrame(filas)

    # ── Filtros ────────────────────────────────────────────────
    numeros = ["Todos"] + sorted({f["N° Solicitud"] for f in filas})
    estados = ["Todos"] + sorted({f["Estado"] for f in filas})
    fc1, fc2, fc3 = st.columns(3)
    filtro_num    = fc1.selectbox("N° Solicitud", numeros, key="st_filtro_num")
    filtro_tarea  = fc2.text_input("Tarea",                key="st_filtro_tarea", placeholder="Buscar...")
    filtro_estado = fc3.selectbox("Estado",       estados, key="st_filtro_est")

    df_f = df.copy()
    if filtro_num != "Todos":
        df_f = df_f[df_f["N° Solicitud"] == filtro_num]
    if filtro_tarea.strip():
        df_f = df_f[df_f["Tarea"].str.contains(filtro_tarea.strip(), case=False, na=False)]
    if filtro_estado != "Todos":
        df_f = df_f[df_f["Estado"] == filtro_estado]
    df_f = df_f.reset_index(drop=True)

    st.data_editor(
        df_f,
        use_container_width=True,
        hide_index=True,
        key="tabla_seg_tareas_v3",
        column_config={
            "☑":            st.column_config.CheckboxColumn("☑",           width="small"),
            "N°":           st.column_config.NumberColumn("N°",             width="small",  disabled=True),
            "N° Solicitud": st.column_config.TextColumn("N° Solicitud",     width="small",  disabled=True),
            "Tarea":        st.column_config.TextColumn("Tarea",            width="large",  disabled=True),

            "Estado":       st.column_config.TextColumn("Estado",           width="medium", disabled=True),
            "Ubicación":    st.column_config.TextColumn("Ubicación",        width="medium", disabled=True),
        },
    )
