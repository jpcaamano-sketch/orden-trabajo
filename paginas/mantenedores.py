"""Página Mantenedores — CRUD de categorías y contactos."""

import pandas as pd
import streamlit as st
import core.queries as q


def render():


    tab_cont, tab_notif, tab_cat = st.tabs(["Contactos", "Notificaciones", "Categorías"])

    # ── Notificaciones por evento ──────────────────────────────
    with tab_notif:
        st.subheader("Notificaciones automáticas")
        st.caption("Define quién recibe correo automático en cada hito del proceso.")

        EVENTO_LABEL = {
            "nueva_solicitud": "Nueva solicitud",
            "planificacion":   "Planificación completada",
            "ejecucion":       "Ejecución completada",
        }
        LABEL_EVENTO = {v: k for k, v in EVENTO_LABEL.items()}
        etapa_opts   = [""] + list(EVENTO_LABEL.values())

        contactos_todos = q.get_contactos(solo_activos=True)
        rut_opts  = [""] + [c["rut"] for c in contactos_todos]
        rut_datos = {c["rut"]: c for c in contactos_todos}

        notif_actuales = q.get_todas_notificaciones()
        _fila_vacia = {"Etapa": "", "RUT": "", "Nombres": "", "Apellidos": "", "Correo": ""}
        df_notif = pd.DataFrame(
            [
                {
                    "Etapa":     EVENTO_LABEL.get(n["evento"], n["evento"]),
                    "RUT":       n["rut"],
                    "Nombres":   n["nombres"],
                    "Apellidos": n["apellidos"],
                    "Correo":    n["correo"],
                }
                for n in notif_actuales
            ] or [_fila_vacia]
        )

        df_notif_ed = st.data_editor(
            df_notif,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="ed_notif",
            column_config={
                "Etapa":     st.column_config.SelectboxColumn("Etapa",     options=etapa_opts, width="medium", required=False),
                "RUT":       st.column_config.SelectboxColumn("RUT",       options=rut_opts,   width="small",  required=False),
                "Nombres":   st.column_config.TextColumn("Nombres",   width="medium", disabled=True),
                "Apellidos": st.column_config.TextColumn("Apellidos", width="medium", disabled=True),
                "Correo":    st.column_config.TextColumn("Correo",    width="medium", disabled=True),
            },
        )

        if st.button("Guardar", key="btn_guardar_notif"):
            errores = [
                i + 1 for i, (_, row) in enumerate(df_notif_ed.iterrows())
                if not str(row.get("Etapa", "")).strip() or not str(row.get("RUT", "")).strip()
            ]
            if errores:
                st.warning(f"Filas {errores}: Etapa y RUT son obligatorios.")
            else:
                filas_nuevas = [
                    {"evento": LABEL_EVENTO[str(row["Etapa"]).strip()], "contacto_rut": str(row["RUT"]).strip()}
                    for _, row in df_notif_ed.iterrows()
                    if LABEL_EVENTO.get(str(row.get("Etapa", "")).strip()) and str(row.get("RUT", "")).strip() in rut_datos
                ]
                q.set_todas_notificaciones(filas_nuevas)
                st.success("Notificaciones guardadas.")
                st.rerun()

    # ── Categorías ─────────────────────────────────────────────
    with tab_cat:
        st.subheader("Categorías de trabajo")

        cats = q.get_categorias()
        cat_ids = [c["id"] for c in cats]
        df_cats = pd.DataFrame([
            {"_id": c["id"], "Categoría": c["nombre"], "Activa": c["activo"]}
            for c in cats
        ])

        df_cats_ed = st.data_editor(
            df_cats,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="ed_cats",
            column_config={
                "_id":      None,
                "Categoría": st.column_config.TextColumn("Categoría", width="large"),
                "Activa":    st.column_config.CheckboxColumn("Activa", width="small", default=True),
            },
        )

        if st.button("Guardar", key="btn_guardar_cats"):
            errores = [
                i + 1 for i, (_, row) in enumerate(df_cats_ed.iterrows())
                if not str(row.get("Categoría", "")).strip()
            ]
            if errores:
                st.warning(f"Filas {errores}: el nombre de la categoría es obligatorio.")
            else:
                for _, row in df_cats_ed.iterrows():
                    nombre = str(row.get("Categoría", "")).strip()
                    activo = bool(row.get("Activa", True))
                    rid = row.get("_id")
                    if pd.notna(rid) and int(rid) in cat_ids:
                        q.actualizar_categoria(int(rid), nombre, activo)
                    else:
                        q.crear_categoria(nombre)
                st.success("Categorías guardadas.")
                st.rerun()

    # ── Contactos ──────────────────────────────────────────────
    with tab_cont:
        st.subheader("Contactos involucrados")

        contactos = [
            c for c in q.get_contactos()
            if c.get("rut") and c.get("nombres")
            and str(c["rut"]).strip() not in ("", "None")
            and str(c["nombres"]).strip() not in ("", "None")
        ]
        cont_ruts = [c["rut"] for c in contactos]
        _cols_cont = {"RUT": "", "Nombres": "", "Apellidos": "", "Empresa": "", "Correo": "", "Teléfono": "", "Activo": True}
        df_conts  = pd.DataFrame(
            [
                {
                    "RUT":       c["rut"],
                    "Nombres":   c.get("nombres") or "",
                    "Apellidos": c.get("apellidos") or "",
                    "Empresa":   c.get("empresa") or "",
                    "Correo":    c.get("correo") or "",
                    "Teléfono":  c.get("telefono") or "",
                    "Activo":    c.get("activo", True),
                }
                for c in contactos
            ] or [_cols_cont]
        )

        df_conts_ed = st.data_editor(
            df_conts,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="ed_conts",
            column_config={
                "RUT":       st.column_config.TextColumn("RUT",       width="small"),
                "Nombres":   st.column_config.TextColumn("Nombres",   width="medium"),
                "Apellidos": st.column_config.TextColumn("Apellidos", width="medium"),
                "Empresa":   st.column_config.TextColumn("Empresa",   width="medium"),
                "Correo":    st.column_config.TextColumn("Correo",    width="medium"),
                "Teléfono":  st.column_config.TextColumn("Teléfono",  width="small"),
                "Activo":    st.column_config.CheckboxColumn("Activo", width="small", default=True),
            },
        )

        if st.button("Guardar", key="btn_guardar_conts"):
            errores = [
                i + 1 for i, (_, row) in enumerate(df_conts_ed.iterrows())
                if not str(row.get("RUT", "")).strip() or not str(row.get("Nombres", "")).strip()
            ]
            if errores:
                st.warning(f"Filas {errores}: RUT y Nombres son obligatorios.")
            else:
                for _, row in df_conts_ed.iterrows():
                    rut       = str(row.get("RUT",       "")).strip()
                    nombres   = str(row.get("Nombres",   "")).strip()
                    apellidos = str(row.get("Apellidos", "")).strip()
                    empresa   = str(row.get("Empresa",   "")).strip()
                    correo    = str(row.get("Correo",    "")).strip()
                    telefono  = str(row.get("Teléfono",  "")).strip()
                    activo    = bool(row.get("Activo", True))
                    if rut in cont_ruts:
                        q.actualizar_contacto(rut, nombres, apellidos, empresa, correo, telefono, activo)
                    else:
                        q.crear_contacto(rut, nombres, apellidos, empresa, correo, telefono)
                st.success("Contactos guardados.")
                st.rerun()
