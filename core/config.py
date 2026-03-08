"""Configuración central — Gestión Órdenes de Trabajo."""

import streamlit as st

def _s(key, default=""):
    try:
        return st.secrets[key]
    except Exception:
        return default

SUPABASE_URL = _s("SUPABASE_URL", "https://efomzdzxkwfmzbturvat.supabase.co")
SUPABASE_KEY = _s("SUPABASE_KEY", (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVmb216ZHp4a3dmbXpidHVydmF0Iiw"
    "icm9sZSI6ImFub24iLCJpYXQiOjE3Njg3NDg1NDIsImV4cCI6MjA4NDMyNDU0Mn0."
    "j0XDhxsBhZpcQ4sGjKLPvbmcMKHxalzfAp7qOdywYQQ"
))

ADMIN_PASSWORD = _s("ADMIN_PASSWORD", "ot2025")

GOOGLE_API_KEY = _s("GOOGLE_API_KEY", "AIzaSyBsx1BEX3SiJHrUjTCBtNdk_0QLvpLOqZc")
APP_VOZ_URL    = _s("APP_VOZ_URL", "http://localhost:8528")

SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = _s("SMTP_USER", "jpcaamano@gmail.com")
SMTP_PASSWORD = _s("SMTP_PASSWORD", "fgwd snko oebq vafx")

ESTADOS_SOLICITUD = ["borrador", "solicitada", "planificada", "en_ejecucion", "completada", "cancelada"]
ESTADOS_TRABAJO   = ["pendiente", "planificado", "en_ejecucion", "completado", "cancelado"]
TIPOS_RECURSO     = ["Personal", "Materiales", "Equipos Pesados", "Equipos Menores"]

LABEL_ESTADO_SOL = {
    "borrador":     "Borrador",
    "solicitada":   "Solicitada",
    "planificada":  "Planificada",
    "en_ejecucion": "En Ejecución",
    "completada":   "Completada",
    "cancelada":    "Cancelada",
}

LABEL_ESTADO_TRAB = {
    "pendiente":    "Solicitado",
    "planificado":  "Planificado",
    "en_ejecucion": "En Ejecución",
    "completado":   "Completado",
    "cancelado":    "Cancelado",
}
