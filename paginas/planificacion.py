"""Página Planificación — tabla de solicitudes + asignación de recursos por trabajo."""

import datetime
import pandas as pd
import streamlit as st
import core.queries as q
from core.email_service import enviar_email_planificacion
from core.styles import alerta
from core.config import TIPOS_RECURSO, LABEL_ESTADO_SOL


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
    st.title("Planificación")

    solicitudes = q.get_solicitudes()
    activas     = [s for s in solicitudes if s["estado"] == "solicitada"]

    if not activas:
        st.info("No hay solicitudes en estado Solicitada pendientes de planificar.")
        return

    hoy = datetime.date.today()

    filas = []
    ids   = []
    for sol in activas:
        trabajos = q.get_trabajos(sol["id"])
        fechas   = [
            _fecha_d(t["fecha_entrega"])
            for t in trabajos
            if t["estado"] != "cancelado" and t.get("fecha_entrega")
        ]
        fecha_min   = min(fechas) if fechas else None
        dias_faltan = (fecha_min - hoy).days if fecha_min else None

        total       = len([t for t in trabajos if t["estado"] != "cancelado"])
        completados = len([t for t in trabajos if t["estado"] == "completado"])
        fechas_term = [_fecha_d(t["fecha_entrega"]) for t in trabajos if t["estado"] == "completado" and t.get("fecha_termino")]
        fecha_ejec  = max(fechas_term) if fechas_term else None

        filas.append({
            "☑":               False,
            "N° Solicitud":    sol["numero"],
            "Fecha visita":    _fmt(sol.get("fecha")),
            "Tareas":          f"{completados} de {total}",
            "Fecha planificada":   _fmt(fecha_min),
            "Días faltantes":  dias_faltan if dias_faltan is not None else "—",
            "Fecha ejecución": _fmt(fecha_ejec),
            "Estado":          LABEL_ESTADO_SOL.get(sol["estado"], sol["estado"]),
        })
        ids.append(sol["id"])

    df = pd.DataFrame(filas)
    df_ed = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        key="tabla_plan",
        column_config={
            "☑":              st.column_config.CheckboxColumn("☑",             width="small"),
            "N° Solicitud":   st.column_config.TextColumn("N° Solicitud",      width="small",  disabled=True),
            "Fecha visita":   st.column_config.TextColumn("Fecha visita",      width="small",  disabled=True),
            "Tareas":         st.column_config.TextColumn("Tareas",            width="small",  disabled=True),
            "Fecha planificada":  st.column_config.TextColumn("Fecha planificada",     width="small",  disabled=True),
            "Días faltantes":  st.column_config.TextColumn("Días faltantes",   width="small",  disabled=True),
            "Fecha ejecución": st.column_config.TextColumn("Fecha ejecución", width="small",  disabled=True),
            "Estado":          st.column_config.TextColumn("Estado",          width="medium", disabled=True),
        },
    )

    seleccionadas = df_ed[df_ed["☑"] == True]
    sol_sel_id    = ids[seleccionadas.index[0]] if len(seleccionadas) == 1 else None

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("Asignar Recursos", use_container_width=True,
                 disabled=sol_sel_id is None, key="btn_asignar"):
        st.session_state["_plan_sol_id"] = sol_sel_id

    # ── Detalle inline ─────────────────────────────────────────
    sol_id = st.session_state.get("_plan_sol_id")
    if not sol_id:
        return

    sol     = q.get_solicitud(sol_id)
    invs    = q.get_involucrados(sol_id)
    activos = [t for t in q.get_trabajos(sol_id) if t["estado"] != "cancelado"]

    st.divider()
    st.subheader(f"{sol['numero']} — Asignación de recursos")

    if not activos:
        st.warning("Esta solicitud no tiene trabajos activos.")
        col_c, _ = st.columns([1, 3])
        if col_c.button("Cerrar", key="btn_cerrar_plan_vacio"):
            del st.session_state["_plan_sol_id"]
            st.rerun()
        return

    # ── Resumen de progreso ────────────────────────────────────
    planificados = sum(1 for t in activos if t["estado"] == "planificado")
    total_act    = len(activos)
    faltan       = total_act - planificados
    if faltan == 0:
        st.success(f"Todas las tareas ({total_act}) tienen fecha y recursos asignados. La solicitud pasará a Ejecución.")
    else:
        st.info(f"{planificados} de {total_act} tareas planificadas. Faltan {faltan} para pasar a Ejecución.")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    trab_data = {}
    for trab in activos:
        cat_nombre = (trab.get("ot_categorias") or {}).get("nombre") or "—"

        with st.expander(f"{trab['descripcion']}  [{cat_nombre}]",
                         expanded=(trab["estado"] != "planificado")):

            fecha_actual = _fecha_d(trab.get("fecha_entrega"))
            ci1, ci2, ci3 = st.columns([2, 2, 3])
            ci1.markdown(
                f"<p style='padding-top:6px;margin:0'><b>Ubicación:</b> {trab.get('ubicacion') or '—'}</p>",
                unsafe_allow_html=True,
            )
            ci2.markdown(
                f"<p style='padding-top:6px;margin:0'><b>Estado:</b> {trab['estado']}</p>",
                unsafe_allow_html=True,
            )
            with ci3:
                lc, ic = st.columns([1.3, 1.7])
                lc.markdown("<p style='padding-top:6px;margin:0'><b>Fecha planificada:</b></p>",
                            unsafe_allow_html=True)
                with ic:
                    fecha_nueva = st.date_input(
                        "", value=fecha_actual,
                        key=f"fecha_{trab['id']}",
                        format="DD/MM/YYYY",
                        label_visibility="collapsed",
                    )

            st.markdown("**Recursos asignados:**")
            recursos = q.get_recursos(trab["id"])
            df_rec = pd.DataFrame(
                [{"Tipo": r["tipo"], "Descripción": r["descripcion"]} for r in recursos]
                or [{"Tipo": TIPOS_RECURSO[0], "Descripción": ""}]
            )
            df_rec.index = range(1, len(df_rec) + 1)
            df_rec_ed = st.data_editor(
                df_rec, num_rows="dynamic", use_container_width=True, hide_index=False,
                key=f"rec_{trab['id']}",
                column_config={
                    "Tipo":        st.column_config.SelectboxColumn("Tipo", options=TIPOS_RECURSO, width="medium", required=True),
                    "Descripción": st.column_config.TextColumn("Descripción", width="large"),
                },
            )

            trab_data[trab["id"]] = {"trab": trab, "fecha": fecha_nueva, "df": df_rec_ed}

    # ── Botones únicos al final ────────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    col_g, col_c = st.columns(2)

    if col_c.button("Cerrar", use_container_width=True, key="btn_cerrar_plan"):
        del st.session_state["_plan_sol_id"]
        st.rerun()

    if col_g.button("Guardar", use_container_width=True, key="btn_guardar_plan"):
        advertencias = []
        guardados    = 0
        for tid, data in trab_data.items():
            fecha      = data["fecha"]
            recursos_v = [row for _, row in data["df"].iterrows() if str(row.get("Descripción", "")).strip()]
            nombre_t   = data["trab"]["descripcion"]

            if not fecha and not recursos_v:
                advertencias.append(f"• {nombre_t}: sin fecha ni recursos.")
                continue
            if not fecha:
                advertencias.append(f"• {nombre_t}: falta fecha planificada.")
                continue
            if not recursos_v:
                advertencias.append(f"• {nombre_t}: faltan recursos.")
                continue

            q.limpiar_recursos(tid)
            for row in recursos_v:
                q.agregar_recurso(tid, str(row.get("Tipo", TIPOS_RECURSO[0])), str(row["Descripción"]).strip())
            q.planificar_trabajo(tid, fecha, sol_id)
            destinatarios = q.get_destinatarios_evento("planificacion", invs)
            try:
                enviar_email_planificacion(
                    sol["numero"], nombre_t, fecha,
                    q.get_recursos(tid), destinatarios,
                )
            except Exception:
                pass
            guardados += 1

        if advertencias:
            st.warning("Tareas sin datos completos (no guardadas):\n" + "\n".join(advertencias))
        if guardados:
            st.success(f"{guardados} tarea(s) planificada(s).")
            st.rerun()
