"""
Ingreso de Solicitudes por Voz — Órdenes de Trabajo
Puerto: 8528 | Acceso público (sin contraseña) | Optimizado para móvil
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import core.queries as q
from core.ai_service import transcribir_y_parsear

st.set_page_config(
    page_title="Nueva Solicitud por Voz",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# CSS mobile-first
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .stApp { background-color: #f0f4f8 !important; }
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stToolbarActions"] { visibility: hidden; }
    .block-container { padding: 1.5rem 1rem 3rem; max-width: 600px; }

    /* Header */
    .voz-header {
        background: linear-gradient(135deg, #1a3a5c 0%, #2d6a9f 100%);
        color: white; border-radius: 16px; padding: 28px 24px 24px;
        text-align: center; margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(26,58,92,0.25);
    }
    .voz-header h1 { font-size: 1.6rem; margin: 0; color: white !important; }
    .voz-header p  { font-size: 0.95rem; margin: 8px 0 0; opacity: 0.85; color: white !important; }

    /* Tarjeta trabajo */
    .trabajo-preview {
        background: white; border-radius: 12px; padding: 16px 18px;
        margin-bottom: 12px; border-left: 5px solid #1a3a5c;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    }

    /* Botones grandes para móvil */
    div.stButton > button {
        background-color: #1a3a5c !important;
        color: white !important; border: none !important;
        border-radius: 12px !important; padding: 0.85rem 1.5rem !important;
        font-weight: 700 !important; font-size: 1rem !important;
        width: 100% !important; transition: all 0.2s ease !important;
    }
    div.stButton > button:hover { background-color: #122a44 !important; }

    /* Botón confirmar verde */
    .btn-confirmar div.stButton > button { background-color: #198754 !important; }
    .btn-confirmar div.stButton > button:hover { background-color: #146c43 !important; }

    /* Botón cancelar */
    .btn-cancelar div.stButton > button {
        background-color: transparent !important;
        color: #dc3545 !important; border: 2px solid #dc3545 !important;
    }

    /* Transcripción */
    .transcripcion-box {
        background: #f8f9fa; border-radius: 10px; padding: 14px 16px;
        border-left: 4px solid #6c757d; margin: 12px 0;
        font-size: 0.92rem; color: #495057; font-style: italic;
    }

    /* Inputs */
    .stTextInput input, .stTextArea textarea {
        border-radius: 10px !important; border: 1px solid #dee2e6 !important;
        font-size: 0.95rem !important;
    }
    .stSelectbox div[data-baseweb="select"] { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────
st.markdown("""
<div class="voz-header">
    <h1>🎙️ Nueva Solicitud</h1>
    <p>Graba un audio describiendo los trabajos que necesitas</p>
</div>
""", unsafe_allow_html=True)

# ── Estado de sesión ───────────────────────────────────────────
if "voz_resultado" not in st.session_state:
    st.session_state.voz_resultado = None
if "voz_confirmado" not in st.session_state:
    st.session_state.voz_confirmado = False

# ── Pantalla de éxito ──────────────────────────────────────────
if st.session_state.voz_confirmado:
    numero = st.session_state.get("voz_numero", "")
    st.success(f"✅ Solicitud **{numero}** creada correctamente.")
    st.markdown("""
    <div style="text-align:center; padding: 20px;">
        <p style="font-size:1.1rem; color:#495057;">
            El equipo revisará tu solicitud y se pondrá en contacto contigo pronto.
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 Crear otra solicitud"):
        st.session_state.voz_resultado   = None
        st.session_state.voz_confirmado  = False
        st.session_state.voz_numero      = ""
        st.rerun()
    st.stop()

# ── Paso 1: Grabar audio ───────────────────────────────────────
if st.session_state.voz_resultado is None:
    st.markdown("### 1️⃣ Graba tu mensaje")
    st.caption("Describe qué trabajos necesitas, dónde y cualquier detalle importante.")

    audio = st.audio_input("Presiona para grabar", key="audio_recorder")

    if audio:
        audio_bytes = audio.read()
        mime_type   = getattr(audio, "type", "audio/webm") or "audio/webm"

        with st.spinner("🤖 Transcribiendo y analizando el audio..."):
            try:
                resultado = transcribir_y_parsear(audio_bytes, mime_type)
                st.session_state.voz_resultado = resultado
                st.rerun()
            except Exception as e:
                st.error(f"Error al procesar el audio: {e}")
                st.caption("Intenta grabar de nuevo con más claridad.")

# ── Paso 2: Revisar y confirmar ────────────────────────────────
else:
    resultado  = st.session_state.voz_resultado
    categorias = q.get_categorias(solo_activas=True)
    cat_nombres = [c["nombre"] for c in categorias]
    cat_map     = {c["nombre"]: c["id"] for c in categorias}
    CATS_VALIDAS = cat_nombres or ["Mantención", "Instalación", "Reparación", "Inspección", "Limpieza"]

    st.markdown("### 2️⃣ Revisa y corrige si es necesario")

    # Transcripción original
    with st.expander("📝 Transcripción original", expanded=False):
        st.markdown(
            f'<div class="transcripcion-box">{resultado.get("transcripcion", "—")}</div>',
            unsafe_allow_html=True,
        )

    # Participantes + Notas
    col_p, col_n = st.columns(2)
    part_edit = col_p.text_area(
        "👥 Participantes",
        value=resultado.get("participantes", ""),
        height=80,
        key="voz_part",
        placeholder="Nombres detectados en el audio...",
    )
    notas_edit = col_n.text_area(
        "📌 Notas generales",
        value=resultado.get("notas", ""),
        height=80,
        key="voz_notas",
    )

    st.markdown("---")
    st.markdown("**🔧 Trabajos detectados**")

    trabajos_raw = resultado.get("trabajos", [])
    if not trabajos_raw:
        trabajos_raw = [{"descripcion": "", "ubicacion": "", "categoria_sugerida": "Otro"}]

    trabajos_editados = []
    for i, t in enumerate(trabajos_raw):
        st.markdown(f"**Trabajo {i+1}**")
        desc = st.text_input(
            "Descripción", value=t.get("descripcion", ""),
            key=f"v_desc_{i}", placeholder="¿Qué se debe hacer?"
        )
        col1, col2 = st.columns(2)
        with col1:
            ubic = st.text_input(
                "Ubicación", value=t.get("ubicacion", ""),
                key=f"v_ubic_{i}", placeholder="Sector, sala, piso..."
            )
        with col2:
            cat_sug = t.get("categoria_sugerida", "")
            if cat_sug not in CATS_VALIDAS:
                cat_sug = CATS_VALIDAS[0] if CATS_VALIDAS else ""
            cat_sel = st.selectbox(
                "Categoría", CATS_VALIDAS,
                index=CATS_VALIDAS.index(cat_sug) if cat_sug in CATS_VALIDAS else 0,
                key=f"v_cat_{i}",
            )
        trabajos_editados.append({
            "descripcion": desc,
            "ubicacion": ubic,
            "categoria_id": cat_map.get(cat_sel),
        })
        if i < len(trabajos_raw) - 1:
            st.markdown("<hr style='margin:8px 0; border-color:#eee;'>", unsafe_allow_html=True)

    st.markdown("---")

    col_ok, col_cancel = st.columns(2)
    with col_ok:
        st.markdown('<div class="btn-confirmar">', unsafe_allow_html=True)
        confirmar = st.button("✅ Confirmar y enviar")
        st.markdown("</div>", unsafe_allow_html=True)
    with col_cancel:
        st.markdown('<div class="btn-cancelar">', unsafe_allow_html=True)
        cancelar = st.button("🗑️ Descartar y grabar de nuevo")
        st.markdown("</div>", unsafe_allow_html=True)

    if cancelar:
        st.session_state.voz_resultado = None
        st.rerun()

    if confirmar:
        validos = [t for t in trabajos_editados if t["descripcion"].strip()]
        if not validos:
            st.warning("Agrega al menos un trabajo con descripción.")
        else:
            sol_id = q.crear_solicitud(notas=notas_edit.strip(), origen="voz")
            q.actualizar_solicitud_participantes(sol_id, part_edit.strip())
            sol    = q.get_solicitud(sol_id)
            for t in validos:
                q.crear_trabajo(sol_id, t["descripcion"].strip(), t.get("ubicacion", "").strip(), t.get("categoria_id"))
            q.recalcular_estado_solicitud(sol_id)
            st.session_state.voz_numero    = sol["numero"]
            st.session_state.voz_confirmado = True
            st.session_state.voz_resultado  = None
            st.rerun()
