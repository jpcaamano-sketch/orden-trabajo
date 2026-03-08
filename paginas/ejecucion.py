"""Página Ejecución — tabla solicitudes + trabajos inline."""

import datetime
import pandas as pd
import streamlit as st
import core.queries as q
from core.email_service import enviar_email_ejecucion_completada
from core.styles import alerta
from core.config import LABEL_ESTADO_SOL, LABEL_ESTADO_TRAB

ESTADOS = ["pendiente", "planificado", "en_ejecucion", "completado", "cancelado"]


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
    st.title("Ejecución")

    solicitudes = q.get_solicitudes()
    activas     = [s for s in solicitudes if s["estado"] in ("planificada", "en_ejecucion")]

    if not activas:
        st.info("No hay solicitudes planificadas para ejecutar.")
        return

    hoy = datetime.date.today()

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
            "N° Solicitud":    sol["numero"],
            "Fecha visita":    _fmt(sol.get("fecha")),
            "Tareas":          f"{completados} de {total}",
            "Fecha planificada":   _fmt(fecha_min),
            "Días faltantes":  dias if dias is not None else "—",
            "Fecha ejecución": _fmt(fecha_ejec),
            "Estado":          LABEL_ESTADO_SOL.get(sol["estado"], sol["estado"]),
        })
        ids.append(sol["id"])

    df = pd.DataFrame(filas)
    df_ed = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        key="tabla_ejec",
        column_config={
            "☑":              st.column_config.CheckboxColumn("☑",            width="small"),
            "N° Solicitud":   st.column_config.TextColumn("N° Solicitud",     width="small",  disabled=True),
            "Fecha visita":   st.column_config.TextColumn("Fecha visita",     width="small",  disabled=True),
            "Tareas":         st.column_config.TextColumn("Tareas",           width="small",  disabled=True),
            "Fecha planificada":  st.column_config.TextColumn("Fecha planificada",    width="small",  disabled=True),
            "Días faltantes":  st.column_config.TextColumn("Días faltantes",   width="small",  disabled=True),
            "Fecha ejecución": st.column_config.TextColumn("Fecha ejecución", width="small",  disabled=True),
            "Estado":          st.column_config.TextColumn("Estado",          width="medium", disabled=True),
        },
    )

    seleccionadas = df_ed[df_ed["☑"] == True]
    sol_sel_id    = ids[seleccionadas.index[0]] if len(seleccionadas) == 1 else None

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("Asignar Fecha Ejecución", use_container_width=True,
                 disabled=sol_sel_id is None, key="btn_ejecutar"):
        st.session_state["_ejec_sol_id"] = sol_sel_id

    # ── Trabajos inline ────────────────────────────────────────
    sol_id = st.session_state.get("_ejec_sol_id")
    if not sol_id:
        return

    sol      = q.get_solicitud(sol_id)
    trabajos = [t for t in q.get_trabajos(sol_id) if t["estado"] != "cancelado"]

    q.recalcular_estado_solicitud(sol_id)

    st.divider()
    st.subheader(f"{sol['numero']} — Trabajos")

    if not trabajos:
        st.warning("Esta solicitud no tiene trabajos activos.")
        return

    df_t = pd.DataFrame([
        {
            "☑":               False,
            "#":               i,
            "_id":             t["id"],
            "_estado_orig":    t["estado"],
            "Tarea":           t["descripcion"],
            "Fecha ejecutado": (
                datetime.date.fromisoformat(t["fecha_termino"])
                if t.get("fecha_termino") else None
            ),
        }
        for i, t in enumerate(trabajos, start=1)
    ])

    df_t_ed = st.data_editor(
        df_t,
        num_rows="fixed",
        use_container_width=True,
        hide_index=True,
        key=f"ed_exec_{sol_id}",
        column_config={
            "☑":               st.column_config.CheckboxColumn("☑",              width="small"),
            "#":               st.column_config.NumberColumn("#",                 width="small",  disabled=True),
            "_id":             None,
            "_estado_orig":    None,
            "Tarea":           st.column_config.TextColumn("Tarea",              width="large",  disabled=True),
            "Fecha ejecutado": st.column_config.DateColumn("Fecha ejecutado",     format="DD-MM-YYYY", width="small"),
        },
    )

    col_guard, col_cerrar = st.columns(2)
    if col_cerrar.button("Cerrar", use_container_width=True, key="btn_cerrar_ejec"):
        del st.session_state["_ejec_sol_id"]
        st.rerun()
    if col_guard.button("Guardar", key="btn_exec_save", use_container_width=True):
        invs                 = q.get_involucrados(sol_id)
        destinatarios        = q.get_destinatarios_evento("ejecucion", invs)
        trabajos_completados = []

        for _, row in df_t_ed.iterrows():
            tid        = int(row["_id"])
            orig_estado = str(row["_estado_orig"])
            ft_raw     = row.get("Fecha ejecutado")
            try:
                ft = None if pd.isnull(ft_raw) else ft_raw
            except Exception:
                ft = ft_raw if ft_raw else None

            nuevo_estado = "completado" if ft else str(row["Estado"])

            if nuevo_estado == orig_estado:
                q.actualizar_trabajo(tid, fecha_termino=str(ft) if ft else None)
                continue

            if nuevo_estado == "en_ejecucion":
                q.iniciar_trabajo(tid, sol_id)
            elif nuevo_estado == "completado":
                q.completar_trabajo(tid, "", ft, sol_id)
                trabajos_completados.append({"desc": row["Tarea"], "ft": ft})
            elif nuevo_estado == "cancelado":
                q.cancelar_trabajo(tid, sol_id)
            else:
                q.actualizar_trabajo(tid, estado=nuevo_estado)

        q.recalcular_estado_solicitud(sol_id)

        for t in trabajos_completados:
            try:
                enviar_email_ejecucion_completada(
                    sol["numero"], t["desc"], t["ft"], "", destinatarios
                )
            except Exception:
                pass

        st.markdown(alerta("Cambios guardados.", "ok"), unsafe_allow_html=True)
        st.rerun()
