"""Página Seguimiento — tabla de solicitudes activas + vista de detalle."""

import datetime
import pandas as pd
import streamlit as st
import core.queries as q
from core.email_service import enviar_email_alerta
from core.styles import alerta
from core.config import LABEL_ESTADO_SOL, LABEL_ESTADO_TRAB


def _fecha_d(val):
    if not val:
        return None
    if isinstance(val, str):
        return datetime.date.fromisoformat(val)
    return val


def _fmt(val):
    if not val or val == "—":
        return "—"
    if hasattr(val, "strftime"):
        return val.strftime("%d-%m-%Y")
    if isinstance(val, str) and len(val) == 10 and val[4] == "-":
        try:
            return datetime.date.fromisoformat(val).strftime("%d-%m-%Y")
        except Exception:
            return val
    return str(val)


def render():


    solicitudes = q.get_solicitudes()
    activas = [s for s in solicitudes if s["estado"] != "borrador"]

    if not activas:
        st.info("No hay solicitudes en seguimiento.")
        return

    hoy   = datetime.date.today()
    ids   = []
    filas = []

    for sol in activas:
        trabajos  = q.get_trabajos(sol["id"])
        activos_t = [t for t in trabajos if t["estado"] != "cancelado"]
        fechas    = [_fecha_d(t["fecha_entrega"]) for t in activos_t if t.get("fecha_entrega")]
        fecha_min = min(fechas) if fechas else None
        dias      = (fecha_min - hoy).days if fecha_min else None

        total       = len([t for t in trabajos if t["estado"] != "cancelado"])
        completados = len([t for t in trabajos if t["estado"] == "completado"])
        fechas_term = [_fecha_d(t["fecha_termino"]) for t in trabajos if t["estado"] == "completado" and t.get("fecha_termino")]
        fecha_ejec  = max(fechas_term) if fechas_term else None

        filas.append({
            "☑":               False,
            "Fecha visita":    _fmt(sol.get("fecha")),
            "N° Solicitud":    sol["numero"],
            "Tareas":          f"{completados} de {total}",
            "Estado":          LABEL_ESTADO_SOL.get(sol["estado"], sol["estado"]),
            "Fecha planificada":   _fmt(fecha_min),
            "Fecha ejecución": _fmt(fecha_ejec),
            "Días faltantes":  dias if dias is not None else "—",
        })
        ids.append(sol["id"])

    df = pd.DataFrame(filas)

    # ── Filtros ────────────────────────────────────────────────
    numeros  = ["Todos"] + sorted([f["N° Solicitud"] for f in filas])
    estados  = ["Todos"] + sorted({f["Estado"] for f in filas})
    fc1, fc2 = st.columns(2)
    filtro_num    = fc1.selectbox("N° Solicitud", numeros,  key="seg_filtro_num")
    filtro_estado = fc2.selectbox("Estado",       estados,  key="seg_filtro_est")

    df_filtrado = df.copy()
    if filtro_num != "Todos":
        df_filtrado = df_filtrado[df_filtrado["N° Solicitud"] == filtro_num]
    if filtro_estado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Estado"] == filtro_estado]

    ids_filtrados = [ids[i] for i in df_filtrado.index]
    df_filtrado   = df_filtrado.reset_index(drop=True)

    df_ed = st.data_editor(
        df_filtrado,
        use_container_width=True,
        hide_index=True,
        key="tabla_seg_v2",
        column_config={
            "☑":               st.column_config.CheckboxColumn("☑",               width="small"),
            "Fecha visita":    st.column_config.TextColumn("Fecha visita",         width="small",  disabled=True),
            "N° Solicitud":    st.column_config.TextColumn("N° Solicitud",         width="small",  disabled=True),
            "Tareas":          st.column_config.TextColumn("Tareas",               width="small",  disabled=True),
            "Estado":          st.column_config.TextColumn("Estado",               width="medium", disabled=True),
            "Fecha planificada": st.column_config.TextColumn("Fecha planificada",  width="small",  disabled=True),
            "Fecha ejecución": st.column_config.TextColumn("Fecha ejecución",      width="small",  disabled=True),
            "Días faltantes":  st.column_config.TextColumn("Días faltantes",       width="small",  disabled=True),
        },
    )

    seleccionadas = df_ed[df_ed["☑"] == True]
    sol_sel_id    = ids_filtrados[seleccionadas.index[0]] if len(seleccionadas) == 1 else None

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("Ver detalle", use_container_width=True,
                 disabled=sol_sel_id is None, key="btn_seguimiento"):
        st.session_state["_seg_sol_id"] = sol_sel_id

    # ── Detalle inline ─────────────────────────────────────────
    sol_id = st.session_state.get("_seg_sol_id")
    if not sol_id:
        return

    sol      = q.get_solicitud(sol_id)
    trabajos = q.get_trabajos(sol_id)
    activos  = [t for t in trabajos if t["estado"] != "cancelado"]

    st.divider()
    st.subheader(f"{sol['numero']} — Seguimiento de trabajos")

    if not activos:
        st.warning("Esta solicitud no tiene trabajos activos.")
        col_c, _ = st.columns([1, 3])
        if col_c.button("Cerrar", key="btn_cerrar_seg_vacio"):
            del st.session_state["_seg_sol_id"]
            st.rerun()
        return

    hoy  = datetime.date.today()
    invs = q.get_involucrados(sol_id)

    filas = []
    for t in activos:
        fe = _fecha_d(t.get("fecha_entrega"))
        atrasado = (
            t["estado"] not in ("completado", "cancelado") and
            fe is not None and fe < hoy
        )
        filas.append({
            "_id":           t["id"],
            "_atrasado":     atrasado,
            "_fe_raw":       fe,
            "Tarea":         t["descripcion"],
            "Ubicación":     t.get("ubicacion") or "—",
            "Estado":        LABEL_ESTADO_TRAB.get(t["estado"], t["estado"]),
            "Fecha planificada": fe,
            "Fecha término": _fecha_d(t.get("fecha_termino")),
        })

    df = pd.DataFrame(filas)

    st.dataframe(
        df.drop(columns=["_id", "_atrasado", "_fe_raw"]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Tarea":         st.column_config.TextColumn("Tarea",         width="large"),
            "Ubicación":     st.column_config.TextColumn("Ubicación",     width="small"),
            "Estado":        st.column_config.TextColumn("Estado",        width="medium"),
            "Fecha planificada": st.column_config.DateColumn("Fecha planificada", format="DD-MM-YYYY", width="small"),
            "Fecha término": st.column_config.DateColumn("Fecha término", format="DD-MM-YYYY", width="small"),
        },
    )

    atrasados = df[df["_atrasado"] == True]
    if not atrasados.empty:
        st.divider()
        st.markdown("**Trabajos atrasados — enviar alerta:**")
        for _, row in atrasados.iterrows():
            fe   = row["_fe_raw"]
            dias = (hoy - fe).days if fe else 0
            c1, c2 = st.columns([7, 1])
            c1.markdown(f"⚠️ **{row['Tarea']}** — {dias} días de atraso")
            if c2.button("Alerta", key=f"alerta_{int(row['_id'])}"):
                destinatarios = q.get_destinatarios_evento("ejecucion", invs)
                try:
                    enviar_email_alerta(sol["numero"], row["Tarea"], str(fe), dias, destinatarios)
                    st.markdown(alerta("Alerta enviada.", "ok"), unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(alerta(f"Error: {e}", "warn"), unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("Cerrar", key="btn_cerrar_seg", use_container_width=True):
        del st.session_state["_seg_sol_id"]
        st.rerun()
