"""Estilos CSS — Gestión Órdenes de Trabajo."""

import streamlit.components.v1 as components  # noqa: F401


def get_css() -> str:
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
        .stApp { background-color: #dde2e8 !important; }
        .stTextInput input, .stTextArea textarea, .stSelectbox > div,
        [data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {
            background-color: #ffffff !important;
        }

        #MainMenu { visibility: hidden; }
        footer    { visibility: hidden; }
        header {
            background-color: #dde2e8 !important;
            border-bottom: none !important;
            box-shadow: none !important;
        }
        header::after {
            content: "Borrador  →  Solicitud  →  Planificación  →  Ejecución";
            position: fixed !important;
            top: 0.6rem !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            color: #dc3545 !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            white-space: nowrap !important;
            pointer-events: none !important;
            z-index: 9999 !important;
        }
        [data-testid="stToolbar"]        { visibility: hidden !important; }
        [data-testid="stToolbarActions"] { visibility: hidden !important; }
        [data-testid="stDecoration"]     { display: none !important; }
        [data-testid="stStatusWidget"]   { display: none !important; }
        [data-testid="collapsedControl"] { visibility: visible !important; display: flex !important; }
        .block-container {
            padding-top: 3.5rem !important;
            padding-bottom: 2rem;
            max-width: 1100px;
        }

        /* Sidebar navy */
        section[data-testid="stSidebar"] {
            background: #1a3a5c !important;
            box-shadow: 4px 0 15px rgba(0,0,0,0.2) !important;
        }
        section[data-testid="stSidebar"] > div {
            background: transparent !important;
            padding-top: 0.5rem !important;
        }
        [data-testid="stSidebar"] * { color: white !important; }
        [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.25); }
        [data-testid="stSidebar"] input[type="radio"]:checked {
            box-shadow: 0 0 0 3px #4fa3e0 !important;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
            border: none !important; padding: 0 !important;
            background: transparent !important; box-shadow: none !important;
        }

        /* Botones */
        div.stButton > button {
            background-color: #1a3a5c !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.6rem 1.2rem !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            transition: all 0.2s ease !important;
        }
        div.stButton > button:hover {
            background-color: #122a44 !important;
            transform: translateY(-1px) !important;
        }

        /* Métricas */
        .metric-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.07);
            border-top: 4px solid #1a3a5c;
        }
        .metric-value {
            font-size: 2.2rem;
            font-weight: 800;
            color: #1a3a5c;
        }
        .metric-label {
            font-size: 0.85rem;
            color: #6c757d;
            margin-top: 4px;
        }

        /* Badges semáforo */
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            white-space: nowrap;
        }
        .badge-verde  { background: #d4edda; color: #155724; }
        .badge-rojo   { background: #f8d7da; color: #721c24; }
        .badge-gris   { background: #e2e3e5; color: #383d41; }
        .badge-amarillo { background: #fff3cd; color: #856404; }

        /* Estado solicitud */
        .estado-borrador    { color: #6c757d; font-weight:600; }
        .estado-planificada { color: #0d6efd; font-weight:600; }
        .estado-en_ejecucion { color: #fd7e14; font-weight:600; }
        .estado-completada  { color: #198754; font-weight:600; }
        .estado-cancelada   { color: #dc3545; font-weight:600; }

        /* Tarjeta trabajo */
        .trabajo-card {
            background: white;
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 10px;
            box-shadow: 0 1px 6px rgba(0,0,0,0.07);
            border-left: 5px solid #1a3a5c;
        }
        .trabajo-card.atrasado { border-left-color: #dc3545; }
        .trabajo-card.completado { border-left-color: #198754; opacity: 0.75; }

        /* Alertas inline */
        .alerta-ok   { background:#d4edda; color:#155724; padding:10px 14px; border-radius:8px;
                       border-left:4px solid #28a745; margin:6px 0; font-size:14px; }
        .alerta-warn { background:#fff3cd; color:#856404; padding:10px 14px; border-radius:8px;
                       border-left:4px solid #ffc107; margin:6px 0; font-size:14px; }
        .alerta-info { background:#cce5ff; color:#004085; padding:10px 14px; border-radius:8px;
                       border-left:4px solid #0d6efd; margin:6px 0; font-size:14px; }
    </style>
    """


def apply_styles(st):
    st.markdown(get_css(), unsafe_allow_html=True)


def metric_card(value, label: str) -> str:
    return f"""
    <div class="metric-card">
        <p class="metric-value">{value}</p>
        <p class="metric-label">{label}</p>
    </div>"""


def badge_semaforo(trabajo: dict) -> str:
    """Retorna HTML badge de semáforo para un trabajo."""
    from datetime import date
    estado = trabajo.get("estado", "")
    if estado == "completado":
        return '<span class="badge badge-gris">✅ Completado</span>'
    if estado == "cancelado":
        return '<span class="badge badge-gris">❌ Cancelado</span>'
    fecha = trabajo.get("fecha_entrega")
    if not fecha:
        return '<span class="badge badge-gris">Sin fecha</span>'
    hoy = date.today()
    from datetime import datetime
    if isinstance(fecha, str):
        fecha_d = datetime.strptime(fecha, "%Y-%m-%d").date()
    else:
        fecha_d = fecha
    delta = (fecha_d - hoy).days
    if delta >= 0:
        return f'<span class="badge badge-verde">En plazo ({delta}d)</span>'
    else:
        return f'<span class="badge badge-rojo">Atrasado ({abs(delta)}d)</span>'


def alerta(mensaje: str, tipo: str = "info") -> str:
    return f'<div class="alerta-{tipo}">{mensaje}</div>'
