"""CRUD completo — Gestión Órdenes de Trabajo."""

from .database import get_client, con_reintento


# ─────────────────────────────────────────────
# CATEGORÍAS
# ─────────────────────────────────────────────

@con_reintento
def get_categorias(solo_activas=False):
    q = get_client().table("ot_categorias").select("*").order("nombre")
    if solo_activas:
        q = q.eq("activo", True)
    return q.execute().data or []


@con_reintento
def crear_categoria(nombre: str):
    get_client().table("ot_categorias").insert({"nombre": nombre}).execute()


@con_reintento
def actualizar_categoria(id: int, nombre: str, activo: bool):
    get_client().table("ot_categorias").update({"nombre": nombre, "activo": activo}).eq("id", id).execute()


# ─────────────────────────────────────────────
# CONTACTOS
# ─────────────────────────────────────────────

@con_reintento
def get_contactos(solo_activos=False):
    q = get_client().table("ot_contactos").select("*").order("nombres")
    if solo_activos:
        q = q.eq("activo", True)
    return q.execute().data or []


@con_reintento
def crear_contacto(rut: str, nombres: str, apellidos: str = "", empresa: str = "", correo: str = "", telefono: str = ""):
    get_client().table("ot_contactos").insert({
        "rut": rut, "nombres": nombres, "apellidos": apellidos,
        "empresa": empresa, "correo": correo, "telefono": telefono,
    }).execute()


@con_reintento
def actualizar_contacto(rut: str, nombres: str, apellidos: str, empresa: str, correo: str, telefono: str, activo: bool):
    get_client().table("ot_contactos").update({
        "nombres": nombres, "apellidos": apellidos, "empresa": empresa,
        "correo": correo, "telefono": telefono, "activo": activo,
    }).eq("rut", rut).execute()


# ─────────────────────────────────────────────
# SOLICITUDES
# ─────────────────────────────────────────────

@con_reintento
def get_solicitudes():
    return (
        get_client().table("ot_solicitudes")
        .select("*, ot_trabajos(id, estado)")
        .order("created_at", desc=True)
        .execute().data or []
    )


@con_reintento
def get_solicitud(id: int):
    rows = (
        get_client().table("ot_solicitudes")
        .select("*")
        .eq("id", id)
        .execute().data
    )
    return rows[0] if rows else None


@con_reintento
def crear_solicitud(notas: str = "", origen: str = "manual", fecha=None) -> int:
    data = {"notas": notas, "origen": origen}
    if fecha:
        data["fecha"] = str(fecha)
    resp = get_client().table("ot_solicitudes").insert(data).execute()
    return resp.data[0]["id"]


@con_reintento
def actualizar_solicitud_notas(id: int, notas: str):
    get_client().table("ot_solicitudes").update({"notas": notas}).eq("id", id).execute()


@con_reintento
def actualizar_solicitud(id: int, notas: str, fecha=None):
    get_client().table("ot_solicitudes").update({
        "notas": notas or None,
        "fecha": str(fecha) if fecha else None,
    }).eq("id", id).execute()


@con_reintento
def actualizar_solicitud_participantes(id: int, participantes: str):
    get_client().table("ot_solicitudes").update({"participantes": participantes}).eq("id", id).execute()


@con_reintento
def aceptar_solicitud(id: int):
    get_client().table("ot_solicitudes").update({"estado": "solicitada"}).eq("id", id).execute()


@con_reintento
def cancelar_solicitud(id: int):
    get_client().table("ot_solicitudes").update({"estado": "cancelada"}).eq("id", id).execute()


@con_reintento
def eliminar_solicitud(id: int):
    get_client().table("ot_solicitudes").delete().eq("id", id).execute()


@con_reintento
def _set_estado_solicitud(id: int, estado: str):
    get_client().table("ot_solicitudes").update({"estado": estado}).eq("id", id).execute()


def recalcular_estado_solicitud(solicitud_id: int):
    """Recalcula y persiste el estado de la solicitud basándose en sus trabajos."""
    sol = get_solicitud(solicitud_id)
    if not sol or sol["estado"] == "cancelada":
        return

    rows = (
        get_client().table("ot_trabajos")
        .select("estado")
        .eq("solicitud_id", solicitud_id)
        .execute().data or []
    )
    activos = [t for t in rows if t["estado"] != "cancelado"]

    if not activos:
        _set_estado_solicitud(solicitud_id, "borrador")
        return

    estados = [t["estado"] for t in activos]

    if all(e == "completado" for e in estados):
        nuevo = "completada"
    elif any(e in ("en_ejecucion", "completado") for e in estados):
        nuevo = "en_ejecucion"
    elif all(e == "planificado" for e in estados):
        nuevo = "planificada"
    else:
        return  # no retroceder si ya está en solicitada o superior

    _set_estado_solicitud(solicitud_id, nuevo)


# ─────────────────────────────────────────────
# TRABAJOS
# ─────────────────────────────────────────────

@con_reintento
def get_trabajos(solicitud_id: int):
    return (
        get_client().table("ot_trabajos")
        .select("*, ot_categorias(nombre)")
        .eq("solicitud_id", solicitud_id)
        .order("created_at")
        .execute().data or []
    )


@con_reintento
def get_trabajo(id: int):
    rows = get_client().table("ot_trabajos").select("*").eq("id", id).execute().data
    return rows[0] if rows else None


@con_reintento
def crear_trabajo(solicitud_id: int, descripcion: str, ubicacion: str = "", categoria_id=None):
    get_client().table("ot_trabajos").insert({
        "solicitud_id": solicitud_id,
        "descripcion":  descripcion,
        "ubicacion":    ubicacion or None,
        "categoria_id": categoria_id or None,
    }).execute()


@con_reintento
def actualizar_trabajo(id: int, **kwargs):
    get_client().table("ot_trabajos").update(kwargs).eq("id", id).execute()


@con_reintento
def eliminar_trabajo(id: int):
    get_client().table("ot_trabajos").delete().eq("id", id).execute()


def planificar_trabajo(id: int, fecha_entrega, solicitud_id: int):
    actualizar_trabajo(id, estado="planificado", fecha_entrega=str(fecha_entrega) if fecha_entrega else None)
    recalcular_estado_solicitud(solicitud_id)


def iniciar_trabajo(id: int, solicitud_id: int):
    actualizar_trabajo(id, estado="en_ejecucion")
    recalcular_estado_solicitud(solicitud_id)


def completar_trabajo(id: int, observacion: str, fecha_termino, solicitud_id: int):
    from datetime import date
    actualizar_trabajo(
        id,
        estado="completado",
        observacion=observacion or None,
        fecha_termino=str(fecha_termino) if fecha_termino else str(date.today()),
    )
    recalcular_estado_solicitud(solicitud_id)


def cancelar_trabajo(id: int, solicitud_id: int):
    actualizar_trabajo(id, estado="cancelado")
    recalcular_estado_solicitud(solicitud_id)


# ─────────────────────────────────────────────
# RECURSOS
# ─────────────────────────────────────────────

@con_reintento
def get_recursos(trabajo_id: int):
    return (
        get_client().table("ot_recursos")
        .select("*")
        .eq("trabajo_id", trabajo_id)
        .order("created_at")
        .execute().data or []
    )


@con_reintento
def agregar_recurso(trabajo_id: int, tipo: str, descripcion: str):
    get_client().table("ot_recursos").insert({
        "trabajo_id": trabajo_id, "tipo": tipo, "descripcion": descripcion
    }).execute()


@con_reintento
def eliminar_recurso(id: int):
    get_client().table("ot_recursos").delete().eq("id", id).execute()


@con_reintento
def limpiar_recursos(trabajo_id: int):
    get_client().table("ot_recursos").delete().eq("trabajo_id", trabajo_id).execute()


# ─────────────────────────────────────────────
# INVOLUCRADOS
# ─────────────────────────────────────────────

@con_reintento
def get_involucrados(solicitud_id: int):
    rows = (
        get_client().table("ot_involucrados")
        .select("*, ot_contactos(rut, nombres, apellidos, correo)")
        .eq("solicitud_id", solicitud_id)
        .execute().data or []
    )
    # Aplanar correo y nombre al nivel raíz para compatibilidad con email_service
    for r in rows:
        cont = r.get("ot_contactos") or {}
        r["correo"] = cont.get("correo")
        r["nombre"] = f"{cont.get('nombres', '')} {cont.get('apellidos', '')}".strip()
    return rows


@con_reintento
def agregar_involucrado(solicitud_id: int, contacto_rut: str):
    get_client().table("ot_involucrados").insert({
        "solicitud_id": solicitud_id,
        "contacto_rut": contacto_rut,
    }).execute()


@con_reintento
def eliminar_involucrado(id: int):
    get_client().table("ot_involucrados").delete().eq("id", id).execute()


# ─────────────────────────────────────────────
# NOTIFICACIONES POR EVENTO
# ─────────────────────────────────────────────
# Eventos fijos: 'nueva_solicitud' | 'planificacion' | 'ejecucion'

@con_reintento
def get_notificaciones_evento(evento: str):
    """Contactos configurados para recibir email en un evento."""
    rows = (
        get_client().table("ot_notificaciones_evento")
        .select("contacto_rut")
        .eq("evento", evento)
        .execute().data or []
    )
    ruts = [r["contacto_rut"] for r in rows]
    if not ruts:
        return []
    return (
        get_client().table("ot_contactos")
        .select("rut, nombres, apellidos, correo")
        .in_("rut", ruts)
        .execute().data or []
    )


@con_reintento
def set_notificaciones_evento(evento: str, contacto_ruts: list):
    """Reemplaza los contactos de notificación para un evento."""
    get_client().table("ot_notificaciones_evento").delete().eq("evento", evento).execute()
    if contacto_ruts:
        get_client().table("ot_notificaciones_evento").insert(
            [{"evento": evento, "contacto_rut": rut} for rut in contacto_ruts]
        ).execute()


@con_reintento
def get_todas_notificaciones():
    """Todas las notificaciones configuradas, con datos del contacto."""
    rows = (
        get_client().table("ot_notificaciones_evento")
        .select("evento, ot_contactos(rut, nombres, apellidos, correo)")
        .execute().data or []
    )
    result = []
    for r in rows:
        c = r.get("ot_contactos") or {}
        result.append({
            "evento":    r["evento"],
            "rut":       c.get("rut", ""),
            "nombres":   c.get("nombres", ""),
            "apellidos": c.get("apellidos", ""),
            "correo":    c.get("correo", ""),
        })
    return result


@con_reintento
def set_todas_notificaciones(rows: list):
    """Reemplaza todas las notificaciones. rows = [{'evento': ..., 'contacto_rut': ...}]"""
    get_client().table("ot_notificaciones_evento").delete().neq("id", 0).execute()
    if rows:
        get_client().table("ot_notificaciones_evento").insert(rows).execute()


def get_destinatarios_evento(evento: str, invs: list = None):
    """Combina involucrados de la solicitud + contactos globales del evento (sin duplicar correos)."""
    invs = invs or []
    globales  = get_notificaciones_evento(evento)
    correos   = {i.get("correo") for i in invs if i.get("correo")}
    extras    = [c for c in globales if c.get("correo") and c["correo"] not in correos]
    return invs + extras
