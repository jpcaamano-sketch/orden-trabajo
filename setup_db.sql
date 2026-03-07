-- ============================================================
-- Gestión Órdenes de Trabajo — Setup DB
-- Prefijo: ot_
-- ============================================================

CREATE TABLE IF NOT EXISTS ot_categorias (
    id         SERIAL PRIMARY KEY,
    nombre     TEXT NOT NULL,
    activo     BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
INSERT INTO ot_categorias (nombre) VALUES
    ('Mantención'),('Instalación'),('Reparación'),('Inspección'),('Limpieza'),('Otro')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS ot_contactos (
    rut        TEXT PRIMARY KEY,
    nombres    TEXT NOT NULL,
    apellidos  TEXT DEFAULT '',
    empresa    TEXT,
    correo     TEXT,
    telefono   TEXT,
    activo     BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ot_solicitudes (
    id         SERIAL PRIMARY KEY,
    numero     TEXT UNIQUE NOT NULL DEFAULT '',
    estado     TEXT NOT NULL DEFAULT 'borrador',
    notas      TEXT,
    origen     TEXT NOT NULL DEFAULT 'manual',  -- 'manual' | 'voz'
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- Para bases existentes:
ALTER TABLE ot_solicitudes ADD COLUMN IF NOT EXISTS origen        TEXT NOT NULL DEFAULT 'manual';
ALTER TABLE ot_solicitudes ADD COLUMN IF NOT EXISTS participantes TEXT;
ALTER TABLE ot_solicitudes ADD COLUMN IF NOT EXISTS fecha         DATE;
CREATE INDEX IF NOT EXISTS idx_ot_solicitudes_estado ON ot_solicitudes(estado);

CREATE SEQUENCE IF NOT EXISTS ot_solicitudes_seq START 1;
CREATE OR REPLACE FUNCTION ot_generar_numero() RETURNS TRIGGER AS $$
BEGIN
    NEW.numero := 'SOL-' || LPAD(nextval('ot_solicitudes_seq')::TEXT, 3, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_ot_numero ON ot_solicitudes;
CREATE TRIGGER trg_ot_numero
    BEFORE INSERT ON ot_solicitudes
    FOR EACH ROW EXECUTE FUNCTION ot_generar_numero();

CREATE TABLE IF NOT EXISTS ot_trabajos (
    id           SERIAL PRIMARY KEY,
    solicitud_id INTEGER NOT NULL REFERENCES ot_solicitudes(id) ON DELETE CASCADE,
    descripcion  TEXT NOT NULL,
    ubicacion    TEXT,
    categoria_id INTEGER REFERENCES ot_categorias(id) ON DELETE SET NULL,
    etapa_id     INTEGER REFERENCES ot_etapas(id)     ON DELETE SET NULL,
    estado       TEXT NOT NULL DEFAULT 'pendiente',
    fecha_entrega DATE,
    fecha_termino DATE,
    observacion  TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ot_trabajos_solicitud ON ot_trabajos(solicitud_id);
CREATE INDEX IF NOT EXISTS idx_ot_trabajos_estado    ON ot_trabajos(estado);

CREATE TABLE IF NOT EXISTS ot_recursos (
    id         SERIAL PRIMARY KEY,
    trabajo_id INTEGER NOT NULL REFERENCES ot_trabajos(id) ON DELETE CASCADE,
    tipo       TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ot_recursos_trabajo ON ot_recursos(trabajo_id);

CREATE TABLE IF NOT EXISTS ot_etapas (
    id     SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ot_involucrados (
    id           SERIAL PRIMARY KEY,
    solicitud_id INTEGER NOT NULL REFERENCES ot_solicitudes(id) ON DELETE CASCADE,
    contacto_rut TEXT    NOT NULL REFERENCES ot_contactos(rut)  ON DELETE CASCADE,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ot_involucrados_solicitud ON ot_involucrados(solicitud_id);

CREATE TABLE IF NOT EXISTS ot_notificaciones_evento (
    id           SERIAL PRIMARY KEY,
    evento       TEXT NOT NULL,  -- 'nueva_solicitud' | 'planificacion' | 'ejecucion'
    contacto_rut TEXT NOT NULL REFERENCES ot_contactos(rut) ON DELETE CASCADE,
    UNIQUE(evento, contacto_rut)
);
