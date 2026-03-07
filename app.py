"""
Gestión Órdenes de Trabajo — YoCreo
Puerto: 8527
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

import streamlit as st
from core.styles import apply_styles

# ── Config página ──────────────────────────────────────────────
st.set_page_config(
    page_title="Órdenes de Trabajo",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_styles(st)

# ── Navegación ─────────────────────────────────────────────────
PAGINAS = [
    "Inicio",
    "Mantenedores",
    "Nueva Solicitud",
    "Planificación",
    "Ejecución",
    "Seguimiento Solicitudes",
    "Seguimiento Tareas",
    "Seguimiento Sol & Tareas",
]

with st.sidebar:
    st.markdown(
        '<a href="http://localhost:8520" target="_self" '
        'style="display:block;color:rgba(255,255,255,0.7);font-size:0.82rem;'
        'text-decoration:none;margin-bottom:8px;">← Volver al Hub</a>',
        unsafe_allow_html=True,
    )
    st.title("🔧 Órdenes de Trabajo")
    st.divider()
    pagina = st.radio("nav", PAGINAS, label_visibility="collapsed", key="nav_radio")
    st.divider()

# Limpiar estado al cambiar de página
if st.session_state.get("_pagina_anterior") != pagina:
    keys_limpiar = [k for k in st.session_state if k not in ("nav_radio", "_pagina_anterior")]
    for k in keys_limpiar:
        del st.session_state[k]
    st.session_state["_pagina_anterior"] = pagina

# ── Enrutador ──────────────────────────────────────────────────
if pagina == "Inicio":
    from paginas.inicio import render
elif pagina == "Mantenedores":
    from paginas.mantenedores import render
elif pagina == "Nueva Solicitud":
    from paginas.solicitud import render
elif pagina == "Planificación":
    from paginas.planificacion import render
elif pagina == "Seguimiento Solicitudes":
    from paginas.seguimiento import render
elif pagina == "Seguimiento Tareas":
    from paginas.seguimiento_tareas import render
elif pagina == "Seguimiento Sol & Tareas":
    from paginas.seguimiento_combinado import render
elif pagina == "Ejecución":
    from paginas.ejecucion import render
else:
    def render():
        st.warning("Página no encontrada.")

render()
