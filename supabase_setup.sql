-- ========================================================
-- YOLO Multi-Class Annotator - Supabase Database Setup
-- ========================================================
-- Este script crea todas las tablas necesarias para el 
-- YOLO Multi-Class Annotator en Supabase (PostgreSQL)
-- ========================================================

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ========================================================
-- 1. TABLA DE USUARIOS
-- ========================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para optimizar búsquedas
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- ========================================================
-- 2. TABLA DE SESIONES DE USUARIO
-- ========================================================

CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    session_name VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Crear índices
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_name ON user_sessions(session_name);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);

-- ========================================================
-- 3. TABLA DE BLACKLIST DE TOKENS (para logout seguro)
-- ========================================================

CREATE TABLE IF NOT EXISTS token_blacklist (
    id SERIAL PRIMARY KEY,
    token VARCHAR(500) UNIQUE NOT NULL,
    blacklisted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Crear índice para optimizar búsquedas de tokens
CREATE INDEX IF NOT EXISTS idx_token_blacklist_token ON token_blacklist(token);
CREATE INDEX IF NOT EXISTS idx_token_blacklist_expires_at ON token_blacklist(expires_at);

-- ========================================================
-- 4. TABLA DE PROYECTOS/DATASETS (Opcional - para futuras versiones)
-- ========================================================

CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- ========================================================
-- 5. TABLA DE CLASES PERSONALIZADAS (ANNOTATION CLASSES)
-- ========================================================

CREATE TABLE IF NOT EXISTS annotation_classes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) NOT NULL DEFAULT '#ff0000', -- Color hex
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_name VARCHAR(255) NULL, -- NULL para clases globales del usuario
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE, -- Para compatibilidad
    is_global BOOLEAN NOT NULL DEFAULT FALSE, -- Solo admin puede crear globales
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_annotation_classes_name_length CHECK (LENGTH(name) >= 1),
    CONSTRAINT chk_annotation_classes_color_format CHECK (color ~ '^#[0-9A-Fa-f]{6}$'),
    CONSTRAINT chk_annotation_classes_name_not_empty CHECK (TRIM(name) != ''),
    
    -- Unique constraint: un usuario no puede tener clases duplicadas por sesión
    CONSTRAINT uk_annotation_classes_user_session_name 
        UNIQUE (user_id, session_name, name) DEFERRABLE INITIALLY DEFERRED
);

-- Índices para annotation_classes
CREATE INDEX IF NOT EXISTS idx_annotation_classes_user_id ON annotation_classes(user_id);
CREATE INDEX IF NOT EXISTS idx_annotation_classes_session_name ON annotation_classes(session_name);
CREATE INDEX IF NOT EXISTS idx_annotation_classes_is_active ON annotation_classes(is_active);
CREATE INDEX IF NOT EXISTS idx_annotation_classes_is_global ON annotation_classes(is_global);
CREATE INDEX IF NOT EXISTS idx_annotation_classes_created_at ON annotation_classes(created_at);

-- Índice compuesto para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_annotation_classes_user_session_active 
    ON annotation_classes(user_id, session_name, is_active);

-- Trigger para updated_at en annotation_classes
CREATE OR REPLACE FUNCTION update_annotation_classes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_annotation_classes_updated_at ON annotation_classes;
CREATE TRIGGER tr_annotation_classes_updated_at
    BEFORE UPDATE ON annotation_classes
    FOR EACH ROW
    EXECUTE FUNCTION update_annotation_classes_updated_at();

-- ========================================================
-- 6. TABLA DE IMÁGENES
-- ========================================================

CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    session_name VARCHAR(255),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_processed BOOLEAN DEFAULT false
);

-- ========================================================
-- 7. TABLA DE ANOTACIONES (Bounding Boxes)
-- ========================================================

CREATE TABLE IF NOT EXISTS annotations (
    id SERIAL PRIMARY KEY,
    image_id INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    class_id INTEGER NOT NULL REFERENCES annotation_classes(id) ON DELETE CASCADE,
    x_center DECIMAL(10, 8) NOT NULL, -- Coordenada X del centro (normalizada 0-1)
    y_center DECIMAL(10, 8) NOT NULL, -- Coordenada Y del centro (normalizada 0-1)
    width DECIMAL(10, 8) NOT NULL,    -- Ancho (normalizado 0-1)
    height DECIMAL(10, 8) NOT NULL,   -- Alto (normalizado 0-1)
    confidence DECIMAL(5, 4) DEFAULT 1.0, -- Confianza de la anotación
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ========================================================
-- 8. TRIGGERS PARA ACTUALIZAR updated_at AUTOMÁTICAMENTE
-- ========================================================

-- Función para actualizar timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Aplicar trigger a las tablas necesarias
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_sessions_updated_at BEFORE UPDATE ON user_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_annotations_updated_at BEFORE UPDATE ON annotations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================================
-- 9. FUNCIONES ÚTILES PARA LIMPIEZA Y GESTIÓN
-- ========================================================

-- Función para limpiar tokens expirados automáticamente
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM token_blacklist 
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Función para crear clases por defecto para un usuario
CREATE OR REPLACE FUNCTION create_default_classes(p_user_id INTEGER, p_session_name VARCHAR DEFAULT NULL)
RETURNS INTEGER AS $$
DECLARE
    created_count INTEGER := 0;
    default_classes RECORD;
BEGIN
    -- Clases por defecto con nombres en español
    FOR default_classes IN 
        SELECT unnest(ARRAY['Persona', 'Vehículo', 'Animal', 'Edificio', 'Objeto', 'Naturaleza']) as name,
               unnest(ARRAY['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff']) as color
    LOOP
        INSERT INTO annotation_classes (name, color, user_id, session_name, is_global, is_active)
        VALUES (default_classes.name, default_classes.color, p_user_id, p_session_name, FALSE, TRUE)
        ON CONFLICT (user_id, session_name, name) DO NOTHING;
        
        IF FOUND THEN
            created_count := created_count + 1;
        END IF;
    END LOOP;
    
    RETURN created_count;
END;
$$ LANGUAGE plpgsql;

-- Función para obtener clases de un usuario con fallback a clases por defecto
CREATE OR REPLACE FUNCTION get_user_classes(p_user_id INTEGER, p_session_name VARCHAR DEFAULT NULL)
RETURNS TABLE(
    id INTEGER,
    name VARCHAR,
    color VARCHAR,
    user_id INTEGER,
    session_name VARCHAR,
    is_global BOOLEAN,
    is_active BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
DECLARE
    class_count INTEGER;
BEGIN
    -- Contar clases existentes
    SELECT COUNT(*) INTO class_count
    FROM annotation_classes 
    WHERE annotation_classes.user_id = p_user_id 
      AND (annotation_classes.session_name = p_session_name OR annotation_classes.session_name IS NULL)
      AND annotation_classes.is_active = TRUE;
    
    -- Si no tiene clases, crear las por defecto
    IF class_count = 0 THEN
        PERFORM create_default_classes(p_user_id, p_session_name);
    END IF;
    
    -- Retornar clases disponibles
    RETURN QUERY
    SELECT 
        ac.id,
        ac.name,
        ac.color,
        ac.user_id,
        ac.session_name,
        ac.is_global,
        ac.is_active,
        ac.created_at
    FROM annotation_classes ac
    WHERE ac.user_id = p_user_id 
      AND (ac.session_name = p_session_name OR ac.session_name IS NULL OR ac.is_global = TRUE)
      AND ac.is_active = TRUE
    ORDER BY ac.created_at;
END;
$$ LANGUAGE plpgsql;

-- Función para importar clases desde anotaciones existentes
CREATE OR REPLACE FUNCTION import_classes_from_annotations(p_user_id INTEGER, p_session_name VARCHAR)
RETURNS INTEGER AS $$
DECLARE
    created_count INTEGER := 0;
    class_id_record RECORD;
    colors TEXT[] := ARRAY['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff', 
                          '#ff8800', '#ff0088', '#8800ff', '#88ff00', '#0088ff', '#00ff88'];
BEGIN
    -- Obtener class_ids únicos de las anotaciones
    FOR class_id_record IN 
        SELECT DISTINCT class_id
        FROM annotations a
        JOIN images i ON a.image_id = i.id
        WHERE i.user_id = p_user_id 
          AND i.session_name = p_session_name
        ORDER BY class_id
    LOOP
        -- Crear clase si no existe
        INSERT INTO annotation_classes (
            name, 
            color, 
            user_id, 
            session_name, 
            is_global, 
            is_active
        )
        VALUES (
            'Clase ' || class_id_record.class_id,
            colors[(class_id_record.class_id % array_length(colors, 1)) + 1],
            p_user_id,
            p_session_name,
            FALSE,
            TRUE
        )
        ON CONFLICT (user_id, session_name, name) DO NOTHING;
        
        IF FOUND THEN
            created_count := created_count + 1;
        END IF;
    END LOOP;
    
    RETURN created_count;
END;
$$ LANGUAGE plpgsql;

-- Función para limpiar datos antiguos (mantenimiento)
CREATE OR REPLACE FUNCTION cleanup_expired_data()
RETURNS TABLE(
    tokens_deleted INTEGER,
    inactive_sessions INTEGER
) AS $$
DECLARE
    token_count INTEGER;
    session_count INTEGER;
BEGIN
    -- Limpiar tokens expirados
    DELETE FROM token_blacklist WHERE expires_at < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS token_count = ROW_COUNT;
    
    -- Contar sesiones inactivas (más de 30 días sin uso)
    SELECT COUNT(*) INTO session_count
    FROM user_sessions 
    WHERE is_active = FALSE 
      AND created_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
    RETURN QUERY SELECT token_count, session_count;
END;
$$ LANGUAGE plpgsql;

-- ========================================================
-- 10. POLÍTICAS DE SEGURIDAD ROW LEVEL SECURITY (RLS)
-- ========================================================

-- Habilitar RLS en las tablas principales
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE images ENABLE ROW LEVEL SECURITY;
ALTER TABLE annotations ENABLE ROW LEVEL SECURITY;
ALTER TABLE annotation_classes ENABLE ROW LEVEL SECURITY;

-- Política para que los usuarios solo vean sus propios datos
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid()::text = id::text OR is_admin = true);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- Política para sesiones de usuario
CREATE POLICY "Users can view own sessions" ON user_sessions
    FOR ALL USING (auth.uid()::text = user_id::text);

-- Política para clases de anotación
CREATE POLICY "Users can view accessible annotation classes" ON annotation_classes
    FOR SELECT USING (
        auth.uid()::text = user_id::text OR 
        is_global = TRUE OR
        EXISTS (
            SELECT 1 FROM users u 
            WHERE u.id::text = auth.uid()::text AND u.is_admin = TRUE
        )
    );

CREATE POLICY "Users can manage own annotation classes" ON annotation_classes
    FOR ALL USING (auth.uid()::text = user_id::text);

CREATE POLICY "Admins can manage global annotation classes" ON annotation_classes
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users u 
            WHERE u.id::text = auth.uid()::text AND u.is_admin = TRUE
        )
    );

-- Política para proyectos
CREATE POLICY "Users can manage own projects" ON projects
    FOR ALL USING (auth.uid()::text = user_id::text);

-- Política para imágenes
CREATE POLICY "Users can manage own images" ON images
    FOR ALL USING (auth.uid()::text = user_id::text);

-- Política para anotaciones
CREATE POLICY "Users can manage own annotations" ON annotations
    FOR ALL USING (auth.uid()::text = user_id::text);

-- Política para clases de anotación
CREATE POLICY "Users can manage own classes" ON annotation_classes
    FOR ALL USING (auth.uid()::text = user_id::text);

-- ========================================================
-- 11. INSERTAR DATOS INICIALES (OPCIONAL)
-- ========================================================

-- Insertar usuario administrador por defecto (cambiar credenciales en producción)
-- NOTA: La contraseña debe ser hasheada por la aplicación antes de insertar
/*
INSERT INTO users (username, email, hashed_password, is_admin) 
VALUES ('admin', 'admin@yolo-annotator.com', '$2b$12$hash_generado_por_la_app', true)
ON CONFLICT (username) DO NOTHING;
*/

-- Insertar algunas clases por defecto para YOLO
/*
INSERT INTO annotation_classes (name, color, user_id) VALUES 
('person', '#FF0000', 1),
('car', '#00FF00', 1),
('bicycle', '#0000FF', 1),
('motorcycle', '#FFFF00', 1),
('bus', '#FF00FF', 1),
('truck', '#00FFFF', 1)
ON CONFLICT DO NOTHING;
*/

-- ========================================================
-- 12. DATOS DE EJEMPLO Y CONFIGURACIÓN INICIAL
-- ========================================================

-- Insertar clases globales por defecto (solo para admin)
-- Estas se pueden usar como plantilla para todos los usuarios
DO $$
BEGIN
    -- Solo insertar si existe el usuario admin (id = 1)
    IF EXISTS (SELECT 1 FROM users WHERE id = 1) THEN
        INSERT INTO annotation_classes (name, color, user_id, session_name, is_global, is_active) VALUES
            ('Persona', '#FF6B6B', 1, NULL, TRUE, TRUE),
            ('Vehículo', '#4ECDC4', 1, NULL, TRUE, TRUE),
            ('Animal', '#45B7D1', 1, NULL, TRUE, TRUE),
            ('Edificio', '#F9CA24', 1, NULL, TRUE, TRUE),
            ('Objeto', '#6C5CE7', 1, NULL, TRUE, TRUE),
            ('Naturaleza', '#A0E7E5', 1, NULL, TRUE, TRUE)
        ON CONFLICT (user_id, session_name, name) DO NOTHING;
    END IF;
END $$;

-- Insertar colores predefinidos como referencia (tabla opcional)
CREATE TABLE IF NOT EXISTS color_presets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    hex_value VARCHAR(7) NOT NULL,
    category VARCHAR(50) DEFAULT 'general',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_color_presets_hex CHECK (hex_value ~ '^#[0-9A-Fa-f]{6}$')
);

INSERT INTO color_presets (name, hex_value, category) VALUES
    ('Rojo', '#ff0000', 'primary'),
    ('Verde', '#00ff00', 'primary'),
    ('Azul', '#0000ff', 'primary'),
    ('Amarillo', '#ffff00', 'primary'),
    ('Magenta', '#ff00ff', 'primary'),
    ('Cian', '#00ffff', 'primary'),
    ('Naranja', '#ff8800', 'secondary'),
    ('Rosa', '#ff0088', 'secondary'),
    ('Púrpura', '#8800ff', 'secondary'),
    ('Verde Lima', '#88ff00', 'secondary'),
    ('Azul Cielo', '#0088ff', 'secondary'),
    ('Turquesa', '#00ff88', 'secondary'),
    ('Rojo Oscuro', '#800000', 'dark'),
    ('Verde Oscuro', '#008000', 'dark'),
    ('Azul Oscuro', '#000080', 'dark'),
    ('Marrón', '#8B4513', 'earth'),
    ('Gris', '#808080', 'neutral'),
    ('Negro', '#000000', 'neutral')
ON CONFLICT DO NOTHING;

-- ========================================================
-- 13. VISTAS ÚTILES
-- ========================================================

-- Vista para estadísticas de usuario
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.created_at,
    COUNT(DISTINCT p.id) as project_count,
    COUNT(DISTINCT i.id) as image_count,
    COUNT(DISTINCT a.id) as annotation_count
FROM users u
LEFT JOIN projects p ON u.id = p.user_id AND p.is_active = true
LEFT JOIN images i ON u.id = i.user_id
LEFT JOIN annotations a ON u.id = a.user_id
GROUP BY u.id, u.username, u.email, u.created_at;

-- Vista para información de proyectos con estadísticas
CREATE OR REPLACE VIEW project_stats AS
SELECT 
    p.id,
    p.name,
    p.description,
    p.user_id,
    u.username as owner_username,
    p.created_at,
    COUNT(DISTINCT i.id) as image_count,
    COUNT(DISTINCT a.id) as annotation_count,
    COUNT(DISTINCT ac.id) as class_count
FROM projects p
JOIN users u ON p.user_id = u.id
LEFT JOIN images i ON p.id = i.project_id
LEFT JOIN annotations a ON i.id = a.image_id
LEFT JOIN annotation_classes ac ON p.id = ac.project_id AND ac.is_active = true
WHERE p.is_active = true
GROUP BY p.id, p.name, p.description, p.user_id, u.username, p.created_at;

-- ========================================================
-- COMENTARIOS FINALES
-- ========================================================

/*
INSTRUCCIONES DE USO:

1. Copia este script completo
2. Ve a tu proyecto de Supabase
3. Abre el "SQL Editor"
4. Pega este script
5. Ejecuta el script
6. Configura las variables de entorno en tu aplicación:
   - SUPABASE_URL=tu_url_de_supabase
   - SUPABASE_ANON_KEY=tu_clave_anon
   - SUPABASE_SERVICE_KEY=tu_clave_service
   - DATABASE_URL=postgresql://postgres:[password]@[host]:[port]/[database]

NOTAS DE SEGURIDAD:
- Cambia las credenciales por defecto
- Revisa las políticas RLS según tus necesidades
- Considera usar Supabase Auth en lugar de JWT personalizado
- Habilita backups automáticos en Supabase

FUNCIONALIDADES INCLUIDAS:
✅ Gestión de usuarios con roles
✅ Sesiones de anotación
✅ Proyectos/datasets
✅ Clases de objetos personalizables
✅ Anotaciones YOLO con coordenadas normalizadas
✅ Blacklist de tokens para logout seguro
✅ Triggers automáticos para timestamps
✅ Políticas de seguridad RLS
✅ Vistas para estadísticas
✅ Funciones de limpieza automática

PRÓXIMOS PASOS:
1. Modificar la aplicación para usar PostgreSQL en lugar de SQLite
2. Actualizar las variables de entorno
3. Probar la conexión
4. Migrar datos existentes si es necesario
*/

-- ========================================================
-- FIN DEL SCRIPT
-- ========================================================
