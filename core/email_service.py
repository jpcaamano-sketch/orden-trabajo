"""Servicio de emails — Gestión Órdenes de Trabajo."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD

_COLOR_NAVY = "#1a3a5c"
_COLOR_ROJO = "#dc3545"


def _enviar_email(destinatario: str, asunto: str, cuerpo_html: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = f"Órdenes de Trabajo <{SMTP_USER}>"
    msg["To"] = destinatario
    msg.attach(MIMEText(cuerpo_html, "html"))
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, destinatario, msg.as_string())


def _plantilla(header_color: str, titulo: str, subtitulo: str, contenido: str) -> str:
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 620px; margin: 0 auto; background:#f4f6f9;">
        <div style="background-color:{header_color}; color:white; padding:28px 24px;
                    text-align:center; border-radius:10px 10px 0 0;">
            <h1 style="margin:0; font-size:22px;">{titulo}</h1>
            <p style="margin:6px 0 0; opacity:0.85; font-size:14px;">{subtitulo}</p>
        </div>
        <div style="padding:30px; background-color:#ffffff; border-radius:0 0 10px 10px;
                    box-shadow:0 2px 8px rgba(0,0,0,0.08);">
            {contenido}
        </div>
        <p style="text-align:center; font-size:11px; color:#9e9e9e; margin-top:16px;">
            Sistema de Gestión de Órdenes de Trabajo — YoCreo
        </p>
    </body>
    </html>
    """


def _emails(involucrados: list) -> list:
    """Extrae correos válidos de una lista de involucrados/contactos."""
    return [i.get("correo") or i.get("email") for i in involucrados if i.get("correo") or i.get("email")]


def enviar_email_solicitud(numero: str, notas: str, trabajos: list, involucrados: list, participantes: str = ""):
    """Email al crear una nueva solicitud — avisa ingreso a Planificación."""
    destinatarios = _emails(involucrados)
    if not destinatarios:
        return

    filas_trabajos = "".join(
        f'<tr><td style="padding:6px 10px; border-bottom:1px solid #eee;">{t["descripcion"]}</td>'
        f'<td style="padding:6px 10px; border-bottom:1px solid #eee; color:#6c757d;">{t.get("ubicacion") or "—"}</td></tr>'
        for t in trabajos
    )
    tabla = f"""
    <table style="width:100%; border-collapse:collapse; margin-top:12px;">
        <thead>
            <tr style="background:{_COLOR_NAVY}; color:white;">
                <th style="padding:8px 10px; text-align:left;">Trabajo</th>
                <th style="padding:8px 10px; text-align:left;">Ubicación</th>
            </tr>
        </thead>
        <tbody>{filas_trabajos}</tbody>
    </table>
    """ if trabajos else "<p style='color:#6c757d;'>Sin trabajos registrados aún.</p>"

    if participantes and participantes.strip():
        import re
        nombres = [n.strip() for n in re.split(r"[,\n]", participantes) if n.strip()]
        filas_part = "".join(
            f'<tr><td style="padding:6px 10px; border-bottom:1px solid #eee;">{n}</td></tr>'
            for n in nombres
        )
        tabla_part = f"""
        <h3 style="color:{_COLOR_NAVY}; margin-top:20px;">Participantes de la visita</h3>
        <table style="width:100%; border-collapse:collapse; margin-top:12px;">
            <thead>
                <tr style="background:{_COLOR_NAVY}; color:white;">
                    <th style="padding:8px 10px; text-align:left;">Nombre</th>
                </tr>
            </thead>
            <tbody>{filas_part}</tbody>
        </table>
        """
    else:
        tabla_part = ""

    contenido = f"""
        <p>Se ha creado una nueva solicitud de trabajo en el sistema.</p>
        <p><strong>Número:</strong> {numero}<br>
           <strong>Notas:</strong> {notas or "—"}</p>
        {tabla_part}
        <h3 style="color:{_COLOR_NAVY}; margin-top:20px;">Trabajos incluidos</h3>
        {tabla}
    """
    asunto = f"Nueva Solicitud — {numero}"
    html = _plantilla(_COLOR_NAVY, f"Nueva Solicitud — {numero}", "Gestión de Órdenes de Trabajo", contenido)
    for email in destinatarios:
        _enviar_email(email, asunto, html)


def enviar_email_planificacion(numero: str, trabajo_desc: str, fecha_entrega, recursos: list, involucrados: list):
    """Email al guardar planificación de un trabajo."""
    destinatarios = _emails(involucrados)
    if not destinatarios:
        return

    fecha_str = str(fecha_entrega) if fecha_entrega else "Sin fecha asignada"
    filas_rec = "".join(
        f'<tr><td style="padding:6px 10px; border-bottom:1px solid #eee;">{r["tipo"]}</td>'
        f'<td style="padding:6px 10px; border-bottom:1px solid #eee;">{r["descripcion"]}</td></tr>'
        for r in recursos
    )
    tabla_rec = f"""
    <table style="width:100%; border-collapse:collapse; margin-top:12px;">
        <thead>
            <tr style="background:{_COLOR_NAVY}; color:white;">
                <th style="padding:8px 10px; text-align:left;">Tipo</th>
                <th style="padding:8px 10px; text-align:left;">Recurso</th>
            </tr>
        </thead>
        <tbody>{filas_rec}</tbody>
    </table>
    """ if recursos else "<p style='color:#6c757d;'>Sin recursos asignados.</p>"

    contenido = f"""
        <p>Se ha registrado la planificación para el siguiente trabajo:</p>
        <p><strong>Solicitud:</strong> {numero}<br>
           <strong>Trabajo:</strong> {trabajo_desc}<br>
           <strong>Fecha de entrega:</strong> {fecha_str}</p>
        <h3 style="color:{_COLOR_NAVY}; margin-top:20px;">Recursos asignados</h3>
        {tabla_rec}
    """
    asunto = f"Planificación asignada — {numero} / {trabajo_desc}"
    html = _plantilla(_COLOR_NAVY, "Planificación asignada", f"{numero} — {trabajo_desc}", contenido)
    for email in destinatarios:
        _enviar_email(email, asunto, html)


def _cabecera_terreno(sol: dict):
    from datetime import date
    numero       = sol.get("numero", "—")
    participantes = sol.get("participantes", "") or ""
    hoy          = date.today()
    dias_es      = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    dia_semana   = dias_es[hoy.weekday()]
    fecha_str    = hoy.strftime("%d/%m/%Y")
    return numero, dia_semana, fecha_str, participantes


def generar_preview_terreno(sol: dict, trabajos: list) -> str:
    """Retorna el HTML del formato para mostrar como preview en pantalla."""
    numero, dia_semana, fecha_str, participantes = _cabecera_terreno(sol)
    return _html_formato_terreno(numero, dia_semana, fecha_str, participantes, trabajos)


def enviar_formato_terreno(sol: dict, trabajos: list, involucrados: list):
    """Genera y envía el formato oficial 'SOLICITUD TRABAJOS EN VISITA A TERRENO'."""
    destinatarios = _emails(involucrados)
    if not destinatarios:
        return 0

    numero, dia_semana, fecha_str, participantes = _cabecera_terreno(sol)
    html   = _html_formato_terreno(numero, dia_semana, fecha_str, participantes, trabajos)
    asunto = f"Solicitud Trabajos en Visita a Terreno — {numero}"
    for email in destinatarios:
        _enviar_email(email, asunto, html)
    return len(destinatarios)


def _filas_participantes(participantes: str) -> str:
    """Genera filas HTML para la tabla de participantes, uno por línea."""
    import re
    # Separar por coma o salto de línea
    nombres = [n.strip() for n in re.split(r"[,\n]", participantes or "") if n.strip()]
    if not nombres:
        return '<tr><td style="border:1px solid #333; padding:7px 10px; text-align:center;">—</td><td style="border:1px solid #333; padding:7px 12px;"></td></tr>'
    filas = ""
    for i, nombre in enumerate(nombres, 1):
        filas += f"""
        <tr>
            <td style="border:1px solid #333; padding:7px 10px; text-align:center; font-size:13px;">{i}</td>
            <td style="border:1px solid #333; padding:7px 12px; font-size:13px;">{nombre}</td>
        </tr>"""
    return filas


def _html_formato_terreno(numero: str, dia_semana: str, fecha_str: str,
                           participantes: str, trabajos: list) -> str:
    """Genera el HTML del formato oficial. Usado tanto para email como para preview en pantalla."""
    filas = ""
    for i, t in enumerate(trabajos, 1):
        cat = (t.get("ot_categorias") or {}).get("nombre") or ""
        filas += f"""
        <tr>
            <td style="border:1px solid #333; padding:7px 10px; text-align:center; font-size:13px;">{i}</td>
            <td style="border:1px solid #333; padding:7px 12px; font-size:13px;">{t.get('descripcion','')}</td>
            <td style="border:1px solid #333; padding:7px 12px; font-size:13px;">{t.get('ubicacion','')}</td>
            <td style="border:1px solid #333; padding:7px 12px; font-size:13px;">{cat}</td>
        </tr>"""

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 30px 40px;
                 background: #ffffff; color: #000000; max-width: 750px; margin: 0 auto;">

        <h2 style="text-align:center; font-weight:bold; font-size:17px;
                   text-transform:uppercase; margin-bottom:28px; letter-spacing:0.5px;">
            Solicitud Trabajos en Visita a Terreno
        </h2>

        <table style="width:100%; margin-bottom:18px; border-collapse:collapse;">
            <tr>
                <td style="font-size:13px; padding:2px 0; width:33%;">
                    <strong>N° Reporte:</strong> {numero}
                </td>
                <td style="font-size:13px; padding:2px 0; width:33%; text-align:center;">
                    <strong>Día:</strong> {dia_semana}
                </td>
                <td style="font-size:13px; padding:2px 0; width:33%; text-align:right;">
                    <strong>Fecha:</strong> {fecha_str}
                </td>
            </tr>
        </table>

        <table style="width:100%; border-collapse:collapse; border:1px solid #333; margin-bottom:18px;">
            <thead>
                <tr>
                    <th colspan="2"
                        style="border:1px solid #333; padding:9px 10px; text-align:center;
                               font-size:13px; font-weight:bold; background:#f0f0f0;">
                        PARTICIPANTES
                    </th>
                </tr>
                <tr>
                    <th style="border:1px solid #333; padding:7px 10px; font-size:13px; font-weight:bold; width:8%;">N°</th>
                    <th style="border:1px solid #333; padding:7px 12px; font-size:13px; font-weight:bold;">Nombre</th>
                </tr>
            </thead>
            <tbody>
                {_filas_participantes(participantes)}
            </tbody>
        </table>

        <table style="width:100%; border-collapse:collapse; border:1px solid #333;">
            <thead>
                <tr>
                    <th colspan="4"
                        style="border:1px solid #333; padding:9px 10px; text-align:center;
                               font-size:13px; font-weight:bold; background:#f0f0f0;">
                        SOLICITUDES
                    </th>
                </tr>
                <tr>
                    <th style="border:1px solid #333; padding:7px 10px; font-size:13px; font-weight:bold; width:8%;">Número</th>
                    <th style="border:1px solid #333; padding:7px 12px; font-size:13px; font-weight:bold; width:46%;">Trabajos</th>
                    <th style="border:1px solid #333; padding:7px 12px; font-size:13px; font-weight:bold; width:26%;">Ubicación</th>
                    <th style="border:1px solid #333; padding:7px 12px; font-size:13px; font-weight:bold; width:20%;">Categoría</th>
                </tr>
            </thead>
            <tbody>{filas}</tbody>
        </table>

        <p style="font-size:11px; color:#888; margin-top:28px; text-align:center;">
            Generado desde Sistema de Gestión de Órdenes de Trabajo — YoCreo
        </p>
    </body>
    </html>
    """


def enviar_email_ejecucion_completada(numero: str, trabajo_desc: str, fecha_termino, observacion: str, involucrados: list):
    """Email al completar la ejecución de un trabajo."""
    destinatarios = _emails(involucrados)
    if not destinatarios:
        return

    fecha_str = str(fecha_termino) if fecha_termino else "—"
    contenido = f"""
        <p>Se ha completado la ejecución del siguiente trabajo:</p>
        <p><strong>Solicitud:</strong> {numero}<br>
           <strong>Trabajo:</strong> {trabajo_desc}<br>
           <strong>Fecha de término:</strong> {fecha_str}</p>
        {"<p><strong>Observación:</strong> " + observacion + "</p>" if observacion else ""}
    """
    asunto = f"Ejecución completada — {numero} / {trabajo_desc}"
    html = _plantilla(_COLOR_NAVY, "Ejecución Completada", f"{numero} — {trabajo_desc}", contenido)
    for email in destinatarios:
        _enviar_email(email, asunto, html)


def enviar_email_alerta(numero: str, trabajo_desc: str, fecha_entrega, dias_atraso: int, involucrados: list):
    """Email de alerta por trabajo atrasado."""
    destinatarios = _emails(involucrados)
    if not destinatarios:
        return

    contenido = f"""
        <p style="color:{_COLOR_ROJO}; font-weight:bold;">⚠️ Este trabajo lleva {dias_atraso} día(s) de atraso.</p>
        <p><strong>Solicitud:</strong> {numero}<br>
           <strong>Trabajo:</strong> {trabajo_desc}<br>
           <strong>Fecha de entrega comprometida:</strong> {fecha_entrega}</p>
        <p>Por favor revisa el estado de este trabajo y toma las acciones necesarias.</p>
    """
    asunto = f"ALERTA: Trabajo atrasado — {numero}"
    html = _plantilla(_COLOR_ROJO, "⚠️ Trabajo Atrasado", f"{numero} — {trabajo_desc}", contenido)
    for email in destinatarios:
        _enviar_email(email, asunto, html)
