"""Página Nueva Solicitud — crear solicitud, trabajos e involucrados."""

import re
import datetime
import pandas as pd
import streamlit as st
import core.queries as q
from core.email_service import enviar_email_solicitud, enviar_formato_terreno
from core.styles import alerta
from core.config import APP_VOZ_URL


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


# ──────────────────────────────────────────────────────────────
# Crear solicitud manual
# ──────────────────────────────────────────────────────────────

def _crear_manual():
    st.subheader("Nueva solicitud manual")

    cats        = q.get_categorias(solo_activas=True)
    cat_nombres = [""] + [c["nombre"] for c in cats]
    cat_map     = {c["nombre"]: c["id"] for c in cats}

    from datetime import date
    c1, c2 = st.columns([2, 1])
    notas      = c1.text_area("Descripción / Notas", key="man_notas", height=80)
    fecha_vis  = c2.date_input("Fecha de visita", value=date.today(), key="man_fecha", format="DD/MM/YYYY")

    # ── Participantes ─────────────────────────────────────────
    st.markdown("**Participantes de la visita**")
    df_part = pd.DataFrame([{"Nombre": ""}])
    df_part_ed = st.data_editor(
        df_part,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="man_participantes",
        column_config={
            "Nombre": st.column_config.TextColumn("Nombre", width="large"),
        },
    )

    # ── Trabajos ──────────────────────────────────────────────
    st.markdown("**Trabajos**")
    df_trab = pd.DataFrame([{"Descripción": "", "Ubicación": "", "Categoría": ""}])
    df_trab_ed = st.data_editor(
        df_trab,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="man_trabajos",
        column_config={
            "Descripción": st.column_config.TextColumn("Descripción", width="large"),
            "Ubicación":   st.column_config.TextColumn("Ubicación",   width="medium"),
            "Categoría":   st.column_config.SelectboxColumn("Categoría", options=cat_nombres, width="medium"),
        },
    )

    if st.button("Crear solicitud", use_container_width=True, key="btn_crear_manual"):
        trabajos_validos = [
            row for _, row in df_trab_ed.iterrows()
            if str(row.get("Descripción", "")).strip()
        ]
        if not trabajos_validos:
            st.warning("Agrega al menos un trabajo con descripción.")
            return

        participantes = ", ".join(
            str(r.get("Nombre", "")).strip()
            for _, r in df_part_ed.iterrows()
            if str(r.get("Nombre", "")).strip()
        )
        sol_id = q.crear_solicitud(notas=notas.strip() or None, origen="manual", fecha=fecha_vis)
        q.actualizar_solicitud_participantes(sol_id, participantes)

        for row in trabajos_validos:
            q.crear_trabajo(
                sol_id,
                str(row["Descripción"]).strip(),
                str(row.get("Ubicación", "")).strip() or None,
                cat_map.get(str(row.get("Categoría", ""))),
            )

        q.recalcular_estado_solicitud(sol_id)

        trabajos_creados = q.get_trabajos(sol_id)
        invs_creados     = q.get_involucrados(sol_id)
        destinatarios    = q.get_destinatarios_evento("nueva_solicitud", invs_creados)
        try:
            enviar_email_solicitud(
                q.get_solicitud(sol_id)["numero"],
                notas.strip() or None,
                trabajos_creados,
                destinatarios,
            )
        except Exception:
            pass

        st.success("Solicitud creada correctamente.")
        st.rerun()


# ──────────────────────────────────────────────────────────────
# Revisión de solicitud de voz — layout 4 secciones
# ──────────────────────────────────────────────────────────────

def _revision_voz(sol_id: int):
    sol      = q.get_solicitud(sol_id)
    trabajos = [t for t in q.get_trabajos(sol_id) if t["estado"] != "cancelado"]
    cats     = q.get_categorias(solo_activas=True)
    cat_nombres = [c["nombre"] for c in cats]
    cat_map     = {c["nombre"]: c["id"] for c in cats}

    # ── Sección 1: Título ──────────────────────────────────────
    with st.container(border=True):
        st.markdown(
            "<h2 style='text-align:center; font-size:1.4rem; font-weight:700; "
            "text-transform:uppercase; letter-spacing:0.5px; margin:4px 0;'>"
            "Solicitud de Trabajo — Visita a Terreno</h2>",
            unsafe_allow_html=True,
        )

    # ── Sección 2: Número, Fecha y Hora ───────────────────────
    from datetime import datetime
    ahora = datetime.now()
    dias_es = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"**N° Solicitud**  \n{sol['numero']}")
        c2.markdown(f"**Fecha**  \n{dias_es[ahora.weekday()]} {ahora.strftime('%d/%m/%Y')}")
        c3.markdown(f"**Hora**  \n{ahora.strftime('%H:%M')}")

    # ── Sección 3: Participantes ───────────────────────────────
    with st.container(border=True):
        st.markdown("**PARTICIPANTES**")
        nombres_raw = re.split(r"[,\n]", sol.get("participantes") or "")
        nombres     = [n.strip() for n in nombres_raw if n.strip()]
        df_part     = pd.DataFrame({"Nombre": nombres if nombres else [""]})

        df_part_ed = st.data_editor(
            df_part,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="ed_participantes",
            column_config={"Nombre": st.column_config.TextColumn("Nombre del participante", width="large")},
        )

    # ── Sección 4: Tabla de trabajos ───────────────────────────
    with st.container(border=True):
        st.markdown("**SOLICITUDES**")
        df_tasks = pd.DataFrame([
            {
                "Tarea":     t["descripcion"],
                "Sector":    t.get("ubicacion") or "",
                "Categoría": (t.get("ot_categorias") or {}).get("nombre") or "",
            }
            for t in trabajos
        ])
        # Índice empieza en 1 (correlativo)
        df_tasks.index = range(1, len(df_tasks) + 1)

        df_tasks_ed = st.data_editor(
            df_tasks,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=False,
            key="ed_tareas",
            column_config={
                "Tarea":     st.column_config.TextColumn("Tarea", width="large"),
                "Sector":    st.column_config.TextColumn("Sector", width="medium"),
                "Categoría": st.column_config.SelectboxColumn(
                    "Categoría", options=cat_nombres, width="medium"
                ),
            },
        )

    # ── Botones guardar / cerrar ───────────────────────────────
    col_g, col_c = st.columns(2)
    if col_g.button("Guardar cambios", use_container_width=True, key="btn_guardar_revision"):
        nuevos_nombres = [str(n).strip() for n in df_part_ed["Nombre"].tolist() if str(n).strip()]
        q.actualizar_solicitud_participantes(sol_id, ", ".join(nuevos_nombres))

        for t in trabajos:
            q.eliminar_trabajo(t["id"])
        for _, row in df_tasks_ed.iterrows():
            desc = str(row.get("Tarea", "")).strip()
            if desc:
                q.crear_trabajo(
                    sol_id,
                    desc,
                    str(row.get("Sector", "")).strip() or None,
                    cat_map.get(str(row.get("Categoría", ""))),
                )
        q.recalcular_estado_solicitud(sol_id)
        st.success("Cambios guardados.")
        st.rerun()
    if col_c.button("Cerrar", use_container_width=True, key="btn_cerrar_revision"):
        del st.session_state["_sol_revision"]
        st.rerun()


# ──────────────────────────────────────────────────────────────
# Editar solicitud existente
# ──────────────────────────────────────────────────────────────

def _editar_solicitud(sol_id: int):
    from datetime import date as date_type
    sol      = q.get_solicitud(sol_id)
    trabajos = [t for t in q.get_trabajos(sol_id) if t["estado"] != "cancelado"]
    cats        = q.get_categorias(solo_activas=True)
    cat_nombres = [""] + [c["nombre"] for c in cats]
    cat_map     = {c["nombre"]: c["id"] for c in cats}

    st.subheader(f"Editando {sol['numero']}")

    c1, c2 = st.columns([2, 1])
    notas     = c1.text_area("Descripción / Notas", value=sol.get("notas") or "", key="edit_notas", height=80)
    fecha_val = date_type.fromisoformat(sol["fecha"]) if sol.get("fecha") else date_type.today()
    fecha_vis = c2.date_input("Fecha de visita", value=fecha_val, key="edit_fecha", format="DD/MM/YYYY")

    # ── Participantes ─────────────────────────────────────────
    st.markdown("**Participantes de la visita**")
    nombres_raw = re.split(r"[,\n]", sol.get("participantes") or "")
    nombres     = [n.strip() for n in nombres_raw if n.strip()]
    df_part     = pd.DataFrame({"Nombre": nombres if nombres else [""]})
    df_part_ed  = st.data_editor(
        df_part, num_rows="dynamic", use_container_width=True, hide_index=True,
        key="edit_participantes",
        column_config={"Nombre": st.column_config.TextColumn("Nombre", width="large")},
    )

    # ── Trabajos ──────────────────────────────────────────────
    st.markdown("**Trabajos**")
    df_tasks = pd.DataFrame([
        {
            "Descripción": t["descripcion"],
            "Ubicación":   t.get("ubicacion") or "",
            "Categoría":   (t.get("ot_categorias") or {}).get("nombre") or "",
        }
        for t in trabajos
    ] or [{"Descripción": "", "Ubicación": "", "Categoría": ""}])
    df_tasks.index = range(1, len(df_tasks) + 1)

    df_tasks_ed = st.data_editor(
        df_tasks, num_rows="dynamic", use_container_width=True, hide_index=False,
        key="edit_tareas",
        column_config={
            "Descripción": st.column_config.TextColumn("Descripción", width="large"),
            "Ubicación":   st.column_config.TextColumn("Ubicación",   width="medium"),
            "Categoría":   st.column_config.SelectboxColumn("Categoría", options=cat_nombres, width="medium"),
        },
    )

    col_g, col_c = st.columns(2)
    if col_g.button("Guardar cambios", use_container_width=True, key="btn_guardar_edicion"):
        trabajos_validos = [
            row for _, row in df_tasks_ed.iterrows()
            if str(row.get("Descripción", "")).strip()
        ]
        if not trabajos_validos:
            st.warning("Agrega al menos un trabajo con descripción.")
            return

        q.actualizar_solicitud(sol_id, notas.strip() or None, fecha_vis)

        participantes = ", ".join(
            str(r.get("Nombre", "")).strip()
            for _, r in df_part_ed.iterrows()
            if str(r.get("Nombre", "")).strip()
        )
        q.actualizar_solicitud_participantes(sol_id, participantes)

        for t in trabajos:
            q.eliminar_trabajo(t["id"])
        for _, row in df_tasks_ed.iterrows():
            desc = str(row.get("Descripción", "")).strip()
            if desc:
                q.crear_trabajo(
                    sol_id, desc,
                    str(row.get("Ubicación", "")).strip() or None,
                    cat_map.get(str(row.get("Categoría", ""))),
                )
        q.recalcular_estado_solicitud(sol_id)
        st.success("Solicitud actualizada.")
        st.rerun()
    if col_c.button("Cerrar", use_container_width=True, key="btn_cerrar_editar"):
        del st.session_state["_sol_editar"]
        st.rerun()


# ──────────────────────────────────────────────────────────────
# Render principal
# ──────────────────────────────────────────────────────────────

def render():
    st.title("Nueva Solicitud")

    tab_listado, tab_manual, tab_voz = st.tabs(["Todas las solicitudes", "Crear manual", "Revisión voz"])

    with tab_listado:
        borradores = [s for s in q.get_solicitudes() if s["estado"] == "borrador"]
        if not borradores:
            st.info("No hay solicitudes en borrador.")
        else:
            ids_todas = [s["id"] for s in borradores]
            df_todas = pd.DataFrame([
                {
                    "☑":           False,
                    "N°":          s["numero"],
                    "Fecha visita": _fmt(s.get("fecha")),
                    "Origen":      "Voz" if s.get("origen") == "voz" else "Manual",
                    "Notas":       s.get("notas") or "—",
                    "Trabajos":    len(s.get("ot_trabajos") or []),
                }
                for s in borradores
            ])
            df_todas_ed = st.data_editor(
                df_todas,
                use_container_width=True,
                hide_index=True,
                key="tabla_todas",
                column_config={
                    "☑":            st.column_config.CheckboxColumn("☑",           width="small"),
                    "N°":           st.column_config.TextColumn("N°",              width="small",  disabled=True),
                    "Fecha visita": st.column_config.TextColumn("Fecha visita",    width="small",  disabled=True),
                    "Origen":       st.column_config.TextColumn("Origen",          width="small",  disabled=True),
                    "Notas":        st.column_config.TextColumn("Notas",           width="large",  disabled=True),
                    "Trabajos":     st.column_config.NumberColumn("Trabajos",      width="small",  disabled=True),
                },
            )

            seleccionadas = df_todas_ed[df_todas_ed["☑"] == True]
            ids_sel = [ids_todas[i] for i in seleccionadas.index]

            col_ac, col_ed, col_del = st.columns(3)
            if col_ac.button("Aceptar", use_container_width=True,
                             disabled=not ids_sel, key="btn_aceptar_sol"):
                sin_fecha = [s["numero"] for s in borradores if s["id"] in ids_sel and not s.get("fecha")]
                if sin_fecha:
                    st.warning(f"Las siguientes solicitudes no tienen fecha de visita: {', '.join(sin_fecha)}. Edítalas antes de aceptar.")
                    st.stop()
                errores = []
                for sid in ids_sel:
                    q.aceptar_solicitud(sid)
                    sol  = q.get_solicitud(sid)
                    from core.database import get_client
                    trabajos = (
                        get_client().table("ot_trabajos")
                        .select("descripcion, ubicacion")
                        .eq("solicitud_id", sid)
                        .execute().data or []
                    )
                    invs = q.get_involucrados(sid)
                    dest = q.get_destinatarios_evento("nueva_solicitud", invs)
                    try:
                        enviar_email_solicitud(sol["numero"], sol.get("notas"), trabajos, dest, sol.get("participantes", ""))
                    except Exception as e:
                        errores.append(str(e))
                st.success(f"{len(ids_sel)} solicitud(es) aceptada(s) — pasan a Planificación.")
                if errores:
                    st.warning(f"Solicitud aceptada pero error al enviar email: {errores[0]}")
                st.rerun()

            if col_ed.button("Editar", use_container_width=True,
                             disabled=len(ids_sel) != 1, key="btn_editar_sol"):
                st.session_state["_sol_editar"] = ids_sel[0]

            if col_del.button("Eliminar", use_container_width=True,
                              disabled=not ids_sel, key="btn_eliminar_sol"):
                for sid in ids_sel:
                    q.eliminar_solicitud(sid)
                st.success(f"{len(ids_sel)} solicitud(es) eliminada(s).")
                st.rerun()

        if "_sol_editar" in st.session_state:
            st.divider()
            _editar_solicitud(st.session_state["_sol_editar"])

    with tab_manual:
        _crear_manual()

    with tab_voz:
        st.markdown(
            f'<a href="{APP_VOZ_URL}" target="_blank" '
            'style="display:inline-block; background:#1a3a5c; color:white; '
            'padding:8px 18px; border-radius:8px; text-decoration:none; '
            'font-size:0.9rem; margin-bottom:16px;">Abrir formulario de voz (móvil)</a>',
            unsafe_allow_html=True,
        )

        solicitudes = q.get_solicitudes()
        pendientes  = [s for s in solicitudes if s.get("origen") == "voz" and s["estado"] == "borrador"]

        if not pendientes:
            st.info("No hay solicitudes pendientes de revisión.")
        else:
            filas = []
            ids   = []
            for sol in pendientes:
                filas.append({
                    "☑":       False,
                    "N°":      sol["numero"],
                    "Resumen": sol.get("notas") or "—",
                })
                ids.append(sol["id"])

            df = pd.DataFrame(filas)
            df_ed = st.data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                key="tabla_pendientes",
                column_config={
                    "☑":       st.column_config.CheckboxColumn("☑", width="small"),
                    "N°":      st.column_config.TextColumn("N°", width="small"),
                    "Resumen": st.column_config.TextColumn("Resumen", width="large"),
                },
                disabled=["N°", "Resumen"],
            )

            seleccionadas = df_ed[df_ed["☑"] == True]
            sol_sel_id    = ids[seleccionadas.index[0]] if not seleccionadas.empty else None

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            col_rev, col_des = st.columns(2)

            if col_rev.button("Revisar", use_container_width=True, disabled=sol_sel_id is None):
                st.session_state["_sol_revision"] = sol_sel_id

            if col_des.button("Descartar", use_container_width=True, disabled=sol_sel_id is None):
                q.cancelar_solicitud(sol_sel_id)
                st.rerun()

        if "_sol_revision" in st.session_state:
            st.divider()
            _revision_voz(st.session_state["_sol_revision"])
