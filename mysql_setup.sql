-- ========================================================
-- YOLO MULTI-CLASS ANNOTATOR - MYSQL DATABASE SETUP
-- ========================================================
-- Compatible con phpMyAdmin y MySQL 5.7+
-- Incluye sistema completo de gestión de clases personalizada
-- Fecha: Septiembre 2025
-- Versión: 2.0 con gestión de clases
-- ========================================================

-- ========================================================
-- 1. CONFIGURACIÓN INICIAL
-- ========================================================

-- Crear base de datos si no existe
CREATE DATABASE IF NOT EXISTS `yolo_annotator` 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `yolo_annotator`;

-- ========================================================
-- 2. TABLA DE USUARIOS
-- ========================================================

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `is_admin` tinyint(1) DEFAULT 0,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_login` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_users_username` (`username`),
  UNIQUE KEY `uk_users_email` (`email`),
  KEY `idx_users_is_active` (`is_active`),
  KEY `idx_users_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================================
-- 3. TABLA DE TOKENS JWT
-- ========================================================

DROP TABLE IF EXISTS `user_tokens`;
CREATE TABLE `user_tokens` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `token_hash` varchar(255) NOT NULL,
  `expires_at` timestamp NOT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `is_revoked` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `fk_user_tokens_user_id` (`user_id`),
  KEY `idx_user_tokens_expires_at` (`expires_at`),
  KEY `idx_user_tokens_token_hash` (`token_hash`),
  CONSTRAINT `fk_user_tokens_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================================
-- 4. TABLA DE PROYECTOS
-- ========================================================

DROP TABLE IF EXISTS `projects`;
CREATE TABLE `projects` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text,
  `user_id` int(11) NOT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_active` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `fk_projects_user_id` (`user_id`),
  KEY `idx_projects_is_active` (`is_active`),
  KEY `idx_projects_created_at` (`created_at`),
  CONSTRAINT `fk_projects_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================================
-- 5. TABLA DE SESIONES DE USUARIO
-- ========================================================

DROP TABLE IF EXISTS `user_sessions`;
CREATE TABLE `user_sessions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `session_name` varchar(100) NOT NULL,
  `user_id` int(11) NOT NULL,
  `project_id` int(11) DEFAULT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_active` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_sessions_name_user` (`session_name`, `user_id`),
  KEY `fk_user_sessions_user_id` (`user_id`),
  KEY `fk_user_sessions_project_id` (`project_id`),
  KEY `idx_user_sessions_is_active` (`is_active`),
  CONSTRAINT `fk_user_sessions_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_user_sessions_project_id` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================================
-- 6. TABLA DE CLASES DE ANOTACIÓN (NUEVA FUNCIONALIDAD)
-- ========================================================

DROP TABLE IF EXISTS `annotation_classes`;
CREATE TABLE `annotation_classes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `project_id` int(11) DEFAULT NULL,
  `name` varchar(50) NOT NULL,
  `color` varchar(7) NOT NULL DEFAULT '#FF0000',
  `session_name` varchar(100) DEFAULT NULL,
  `is_global` tinyint(1) DEFAULT 0,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_annotation_classes_user_session_name` (`user_id`, `session_name`, `name`),
  KEY `fk_annotation_classes_user_id` (`user_id`),
  KEY `fk_annotation_classes_project_id` (`project_id`),
  KEY `idx_annotation_classes_session_name` (`session_name`),
  KEY `idx_annotation_classes_is_active` (`is_active`),
  KEY `idx_annotation_classes_is_global` (`is_global`),
  KEY `idx_annotation_classes_created_at` (`created_at`),
  KEY `idx_annotation_classes_user_session_active` (`user_id`, `session_name`, `is_active`),
  CONSTRAINT `fk_annotation_classes_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_annotation_classes_project_id` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE SET NULL,
  CONSTRAINT `chk_annotation_classes_name_length` CHECK (CHAR_LENGTH(TRIM(`name`)) >= 1),
  CONSTRAINT `chk_annotation_classes_name_not_empty` CHECK (TRIM(`name`) != ''),
  CONSTRAINT `chk_annotation_classes_color_format` CHECK (`color` REGEXP '^#[0-9A-Fa-f]{6}$')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================================
-- 7. TABLA DE IMÁGENES
-- ========================================================

DROP TABLE IF EXISTS `images`;
CREATE TABLE `images` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) NOT NULL,
  `original_filename` varchar(255) NOT NULL,
  `file_path` varchar(500) NOT NULL,
  `file_size` bigint(20) DEFAULT NULL,
  `width` int(11) DEFAULT NULL,
  `height` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  `project_id` int(11) DEFAULT NULL,
  `session_name` varchar(100) DEFAULT NULL,
  `uploaded_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `is_annotated` tinyint(1) DEFAULT 0,
  `annotation_count` int(11) DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_images_filename_user` (`filename`, `user_id`),
  KEY `fk_images_user_id` (`user_id`),
  KEY `fk_images_project_id` (`project_id`),
  KEY `idx_images_session_name` (`session_name`),
  KEY `idx_images_uploaded_at` (`uploaded_at`),
  KEY `idx_images_is_annotated` (`is_annotated`),
  CONSTRAINT `fk_images_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_images_project_id` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================================
-- 8. TABLA DE ANOTACIONES
-- ========================================================

DROP TABLE IF EXISTS `annotations`;
CREATE TABLE `annotations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `image_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `class_id` int(11) DEFAULT NULL,
  `class_name` varchar(50) NOT NULL,
  `x_center` decimal(10,8) NOT NULL,
  `y_center` decimal(10,8) NOT NULL,
  `width` decimal(10,8) NOT NULL,
  `height` decimal(10,8) NOT NULL,
  `confidence` decimal(5,4) DEFAULT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_annotations_image_id` (`image_id`),
  KEY `fk_annotations_user_id` (`user_id`),
  KEY `fk_annotations_class_id` (`class_id`),
  KEY `idx_annotations_class_name` (`class_name`),
  KEY `idx_annotations_created_at` (`created_at`),
  CONSTRAINT `fk_annotations_image_id` FOREIGN KEY (`image_id`) REFERENCES `images` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_annotations_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_annotations_class_id` FOREIGN KEY (`class_id`) REFERENCES `annotation_classes` (`id`) ON DELETE SET NULL,
  CONSTRAINT `chk_annotations_coordinates` CHECK (
    `x_center` >= 0 AND `x_center` <= 1 AND
    `y_center` >= 0 AND `y_center` <= 1 AND
    `width` > 0 AND `width` <= 1 AND
    `height` > 0 AND `height` <= 1
  ),
  CONSTRAINT `chk_annotations_confidence` CHECK (`confidence` IS NULL OR (`confidence` >= 0 AND `confidence` <= 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================================
-- 9. TABLA DE HISTORIAL DE ACTIVIDADES
-- ========================================================

DROP TABLE IF EXISTS `activity_log`;
CREATE TABLE `activity_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `action` varchar(50) NOT NULL,
  `resource_type` varchar(50) NOT NULL,
  `resource_id` int(11) DEFAULT NULL,
  `details` json DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` text,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_activity_log_user_id` (`user_id`),
  KEY `idx_activity_log_action` (`action`),
  KEY `idx_activity_log_resource_type` (`resource_type`),
  KEY `idx_activity_log_created_at` (`created_at`),
  CONSTRAINT `fk_activity_log_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================================
-- 10. TRIGGERS PARA ACTUALIZACIÓN AUTOMÁTICA
-- ========================================================

-- Trigger para actualizar annotation_count en images
DELIMITER $$
CREATE TRIGGER `tr_annotations_insert_update_count` 
AFTER INSERT ON `annotations`
FOR EACH ROW
BEGIN
    UPDATE `images` 
    SET `annotation_count` = (
        SELECT COUNT(*) FROM `annotations` WHERE `image_id` = NEW.`image_id`
    ),
    `is_annotated` = 1
    WHERE `id` = NEW.`image_id`;
END$$

CREATE TRIGGER `tr_annotations_delete_update_count` 
AFTER DELETE ON `annotations`
FOR EACH ROW
BEGIN
    DECLARE ann_count INT DEFAULT 0;
    
    SELECT COUNT(*) INTO ann_count 
    FROM `annotations` 
    WHERE `image_id` = OLD.`image_id`;
    
    UPDATE `images` 
    SET `annotation_count` = ann_count,
        `is_annotated` = IF(ann_count > 0, 1, 0)
    WHERE `id` = OLD.`image_id`;
END$$
DELIMITER ;

-- ========================================================
-- 11. STORED PROCEDURES PARA GESTIÓN DE CLASES
-- ========================================================

-- Procedure para crear clases por defecto
DELIMITER $$
CREATE PROCEDURE `sp_CreateDefaultClasses`(
    IN p_user_id INT,
    IN p_session_name VARCHAR(100)
)
BEGIN
    DECLARE v_project_id INT DEFAULT NULL;
    
    -- Obtener project_id si existe la sesión
    SELECT project_id INTO v_project_id 
    FROM user_sessions 
    WHERE user_id = p_user_id AND session_name = p_session_name 
    LIMIT 1;
    
    -- Insertar clases por defecto
    INSERT INTO annotation_classes (user_id, project_id, name, color, session_name, is_global, is_active) VALUES
    (p_user_id, v_project_id, 'person', '#FF0000', p_session_name, 0, 1),
    (p_user_id, v_project_id, 'bicycle', '#00FF00', p_session_name, 0, 1),
    (p_user_id, v_project_id, 'car', '#0000FF', p_session_name, 0, 1),
    (p_user_id, v_project_id, 'motorcycle', '#FFFF00', p_session_name, 0, 1),
    (p_user_id, v_project_id, 'airplane', '#FF00FF', p_session_name, 0, 1),
    (p_user_id, v_project_id, 'bus', '#00FFFF', p_session_name, 0, 1),
    (p_user_id, v_project_id, 'train', '#FFA500', p_session_name, 0, 1),
    (p_user_id, v_project_id, 'truck', '#800080', p_session_name, 0, 1),
    (p_user_id, v_project_id, 'boat', '#008000', p_session_name, 0, 1),
    (p_user_id, v_project_id, 'dog', '#FFC0CB', p_session_name, 0, 1),
    (p_user_id, v_project_id, 'cat', '#A52A2A', p_session_name, 0, 1),
    (p_user_id, v_project_id, 'bird', '#808080', p_session_name, 0, 1)
    ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;
    
    SELECT ROW_COUNT() as classes_created;
END$$

-- Procedure para obtener clases de usuario
CREATE PROCEDURE `sp_GetUserClasses`(
    IN p_user_id INT,
    IN p_session_name VARCHAR(100),
    IN p_include_global BOOLEAN
)
BEGIN
    SELECT 
        id,
        user_id,
        project_id,
        name,
        color,
        session_name,
        is_global,
        is_active,
        created_at,
        updated_at,
        CASE 
            WHEN is_global = 1 THEN 'Global'
            WHEN session_name IS NULL THEN 'General'
            ELSE CONCAT('Session: ', session_name)
        END as scope
    FROM annotation_classes
    WHERE 
        (user_id = p_user_id OR (is_global = 1 AND p_include_global = 1))
        AND (session_name = p_session_name OR session_name IS NULL OR is_global = 1)
        AND is_active = 1
    ORDER BY is_global DESC, session_name ASC, name ASC;
END$$

-- Procedure para estadísticas de clases
CREATE PROCEDURE `sp_GetClassStatistics`(
    IN p_user_id INT
)
BEGIN
    SELECT 
        u.username,
        COUNT(ac.id) as total_classes,
        COUNT(CASE WHEN ac.is_active = 1 THEN 1 END) as active_classes,
        COUNT(CASE WHEN ac.session_name IS NULL THEN 1 END) as general_classes,
        COUNT(DISTINCT ac.session_name) as sessions_with_classes,
        MAX(ac.created_at) as last_class_created,
        COUNT(CASE WHEN ac.is_global = 1 THEN 1 END) as global_classes
    FROM users u
    LEFT JOIN annotation_classes ac ON u.id = ac.user_id
    WHERE u.id = p_user_id
    GROUP BY u.id, u.username;
END$$

-- Procedure para limpiar tokens expirados
CREATE PROCEDURE `sp_CleanupExpiredTokens`()
BEGIN
    DELETE FROM user_tokens 
    WHERE expires_at < NOW() OR is_revoked = 1;
    
    SELECT ROW_COUNT() as tokens_deleted;
END$$
DELIMITER ;

-- ========================================================
-- 12. VISTAS PARA REPORTES Y ESTADÍSTICAS
-- ========================================================

-- Vista: Estadísticas de usuarios
CREATE OR REPLACE VIEW `vw_user_statistics` AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.is_active,
    u.is_admin,
    u.created_at,
    u.last_login,
    COUNT(DISTINCT p.id) as total_projects,
    COUNT(DISTINCT us.id) as total_sessions,
    COUNT(DISTINCT i.id) as total_images,
    COUNT(DISTINCT a.id) as total_annotations,
    COUNT(DISTINCT ac.id) as total_classes
FROM users u
LEFT JOIN projects p ON u.id = p.user_id
LEFT JOIN user_sessions us ON u.id = us.user_id
LEFT JOIN images i ON u.id = i.user_id
LEFT JOIN annotations a ON u.id = a.user_id
LEFT JOIN annotation_classes ac ON u.id = ac.user_id
GROUP BY u.id, u.username, u.email, u.is_active, u.is_admin, u.created_at, u.last_login;

-- Vista: Estadísticas de proyectos
CREATE OR REPLACE VIEW `vw_project_statistics` AS
SELECT 
    p.id,
    p.name,
    p.description,
    u.username as created_by,
    p.created_at,
    p.is_active,
    COUNT(DISTINCT i.id) as total_images,
    COUNT(DISTINCT a.id) as total_annotations,
    COUNT(DISTINCT ac.id) as total_classes,
    AVG(i.annotation_count) as avg_annotations_per_image
FROM projects p
INNER JOIN users u ON p.user_id = u.id
LEFT JOIN images i ON p.id = i.project_id
LEFT JOIN annotations a ON i.id = a.image_id
LEFT JOIN annotation_classes ac ON p.id = ac.project_id
GROUP BY p.id, p.name, p.description, u.username, p.created_at, p.is_active;

-- Vista: Estadísticas de clases por usuario
CREATE OR REPLACE VIEW `vw_class_stats_by_user` AS
SELECT 
    u.id as user_id,
    u.username,
    COUNT(ac.id) as total_classes,
    COUNT(CASE WHEN ac.is_active = 1 THEN 1 END) as active_classes,
    COUNT(CASE WHEN ac.session_name IS NULL THEN 1 END) as general_classes,
    COUNT(DISTINCT ac.session_name) as sessions_with_classes,
    MAX(ac.created_at) as last_class_created,
    COUNT(CASE WHEN ac.is_global = 1 THEN 1 END) as global_classes
FROM users u
LEFT JOIN annotation_classes ac ON u.id = ac.user_id
GROUP BY u.id, u.username;

-- Vista: Clases más populares
CREATE OR REPLACE VIEW `vw_popular_classes` AS
SELECT 
    ac.name,
    ac.color,
    COUNT(DISTINCT ac.user_id) as used_by_users,
    COUNT(ac.id) as total_instances,
    COUNT(CASE WHEN ac.is_active = 1 THEN 1 END) as active_instances,
    AVG(CASE WHEN ac.is_active = 1 THEN 1.0 ELSE 0.0 END) as active_percentage,
    COUNT(DISTINCT a.id) as annotation_usage
FROM annotation_classes ac
LEFT JOIN annotations a ON ac.id = a.class_id
GROUP BY ac.name, ac.color
HAVING COUNT(ac.id) > 0
ORDER BY used_by_users DESC, total_instances DESC;

-- Vista: Resumen de gestión de clases
CREATE OR REPLACE VIEW `vw_class_management_summary` AS
SELECT 
    ac.id,
    ac.name,
    ac.color,
    u.username as created_by,
    ac.session_name,
    ac.is_global,
    ac.is_active,
    ac.created_at,
    ac.updated_at,
    CASE 
        WHEN ac.is_global = 1 THEN 'Global'
        WHEN ac.session_name IS NULL THEN 'General'
        ELSE CONCAT('Session: ', ac.session_name)
    END as scope,
    DATEDIFF(NOW(), ac.created_at) as days_old,
    COUNT(a.id) as annotation_count
FROM annotation_classes ac
INNER JOIN users u ON ac.user_id = u.id
LEFT JOIN annotations a ON ac.id = a.class_id
GROUP BY ac.id, ac.name, ac.color, u.username, ac.session_name, 
         ac.is_global, ac.is_active, ac.created_at, ac.updated_at;

-- Vista: Sesiones activas
CREATE OR REPLACE VIEW `vw_active_sessions` AS
SELECT 
    us.id,
    us.session_name,
    us.user_id,
    u.username,
    us.created_at,
    COUNT(DISTINCT i.id) as image_count,
    MAX(i.uploaded_at) as last_image_upload,
    COUNT(DISTINCT ac.id) as class_count
FROM user_sessions us
INNER JOIN users u ON us.user_id = u.id
LEFT JOIN images i ON us.session_name = i.session_name AND us.user_id = i.user_id
LEFT JOIN annotation_classes ac ON us.session_name = ac.session_name AND us.user_id = ac.user_id
WHERE us.is_active = 1
GROUP BY us.id, us.session_name, us.user_id, u.username, us.created_at;

-- ========================================================
-- 13. DATOS DE EJEMPLO Y CONFIGURACIÓN INICIAL
-- ========================================================

-- Insertar usuario administrador por defecto
INSERT INTO `users` (`username`, `email`, `password_hash`, `is_active`, `is_admin`) 
VALUES ('admin', 'admin@yolo-annotator.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0WS8P5Vda6', 1, 1)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- Insertar usuario de prueba
INSERT INTO `users` (`username`, `email`, `password_hash`, `is_active`, `is_admin`) 
VALUES ('testuser', 'test@yolo-annotator.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0WS8P5Vda6', 1, 0)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- Crear proyecto de ejemplo
INSERT INTO `projects` (`name`, `description`, `user_id`) 
VALUES ('Proyecto Demo', 'Proyecto de demostración para YOLO Annotator', 1)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- Crear sesión de ejemplo
INSERT INTO `user_sessions` (`session_name`, `user_id`, `project_id`) 
VALUES ('demo_session', 1, 1)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- Crear clases globales por defecto
INSERT INTO `annotation_classes` (`user_id`, `project_id`, `name`, `color`, `session_name`, `is_global`, `is_active`) VALUES
(1, NULL, 'person', '#FF0000', NULL, 1, 1),
(1, NULL, 'vehicle', '#00FF00', NULL, 1, 1),
(1, NULL, 'animal', '#0000FF', NULL, 1, 1),
(1, NULL, 'object', '#FFFF00', NULL, 1, 1)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- Crear tabla de colores predefinidos
CREATE TABLE IF NOT EXISTS `color_presets` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `hex_value` varchar(7) NOT NULL,
  `category` varchar(50) DEFAULT 'general',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_color_presets_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertar colores predefinidos
INSERT INTO `color_presets` (`name`, `hex_value`, `category`) VALUES
('Rojo', '#FF0000', 'basicos'),
('Verde', '#00FF00', 'basicos'),
('Azul', '#0000FF', 'basicos'),
('Amarillo', '#FFFF00', 'basicos'),
('Magenta', '#FF00FF', 'basicos'),
('Cian', '#00FFFF', 'basicos'),
('Naranja', '#FFA500', 'calidos'),
('Rosa', '#FFC0CB', 'calidos'),
('Violeta', '#800080', 'frios'),
('Verde Oscuro', '#008000', 'frios'),
('Azul Marino', '#000080', 'frios'),
('Marrón', '#A52A2A', 'neutros'),
('Gris', '#808080', 'neutros'),
('Negro', '#000000', 'neutros'),
('Blanco', '#FFFFFF', 'neutros')
ON DUPLICATE KEY UPDATE hex_value = VALUES(hex_value);

-- ========================================================
-- 14. EVENTOS PARA MANTENIMIENTO AUTOMÁTICO
-- ========================================================

-- Habilitar el scheduler de eventos
SET GLOBAL event_scheduler = ON;

-- Evento para limpiar tokens expirados cada hora
CREATE EVENT IF NOT EXISTS `ev_cleanup_expired_tokens`
ON SCHEDULE EVERY 1 HOUR
STARTS CURRENT_TIMESTAMP
DO
  CALL sp_CleanupExpiredTokens();

-- Evento para actualizar estadísticas diarias
CREATE EVENT IF NOT EXISTS `ev_update_daily_stats`
ON SCHEDULE EVERY 1 DAY
STARTS (CURRENT_DATE + INTERVAL 1 DAY + INTERVAL 2 HOUR)
DO
BEGIN
    -- Actualizar contadores de anotaciones
    UPDATE images i SET 
        annotation_count = (SELECT COUNT(*) FROM annotations WHERE image_id = i.id),
        is_annotated = (SELECT COUNT(*) FROM annotations WHERE image_id = i.id) > 0;
    
    -- Log de mantenimiento
    INSERT INTO activity_log (user_id, action, resource_type, details) 
    VALUES (1, 'MAINTENANCE', 'SYSTEM', JSON_OBJECT('event', 'daily_stats_update'));
END;

-- ========================================================
-- 15. ÍNDICES ADICIONALES PARA OPTIMIZACIÓN
-- ========================================================

-- Índices compuestos para consultas frecuentes
CREATE INDEX `idx_annotations_image_class` ON `annotations` (`image_id`, `class_id`);
CREATE INDEX `idx_annotations_user_created` ON `annotations` (`user_id`, `created_at`);
CREATE INDEX `idx_images_user_session` ON `images` (`user_id`, `session_name`);
CREATE INDEX `idx_user_sessions_user_active` ON `user_sessions` (`user_id`, `is_active`);

-- ========================================================
-- 16. CONFIGURACIÓN DE SEGURIDAD
-- ========================================================

-- Crear usuario específico para la aplicación (ejecutar manualmente)
-- CREATE USER 'yolo_app'@'localhost' IDENTIFIED BY 'password_seguro_aqui';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON yolo_annotator.* TO 'yolo_app'@'localhost';
-- GRANT EXECUTE ON yolo_annotator.* TO 'yolo_app'@'localhost';
-- FLUSH PRIVILEGES;

-- ========================================================
-- 17. VERIFICACIÓN FINAL
-- ========================================================

-- Mostrar resumen de instalación
SELECT 'INSTALACIÓN COMPLETADA' as status;

SELECT 
    'Tablas creadas: ' as descripcion,
    COUNT(*) as cantidad
FROM information_schema.tables 
WHERE table_schema = 'yolo_annotator';

SELECT 
    'Índices creados: ' as descripcion,
    COUNT(*) as cantidad
FROM information_schema.statistics 
WHERE table_schema = 'yolo_annotator';

SELECT 
    'Procedures creados: ' as descripcion,
    COUNT(*) as cantidad
FROM information_schema.routines 
WHERE routine_schema = 'yolo_annotator' 
AND routine_type = 'PROCEDURE';

SELECT 
    'Vistas creadas: ' as descripcion,
    COUNT(*) as cantidad
FROM information_schema.views 
WHERE table_schema = 'yolo_annotator';

SELECT 
    'Eventos programados: ' as descripcion,
    COUNT(*) as cantidad
FROM information_schema.events 
WHERE event_schema = 'yolo_annotator';

-- ========================================================
-- COMENTARIOS FINALES
-- ========================================================

/*
INSTRUCCIONES DE USO EN PHPMYADMIN:

1. PREPARACIÓN:
   - Abrir phpMyAdmin
   - Ir a la pestaña "SQL"
   - Copiar y pegar este script completo
   - Ejecutar

2. CONFIGURACIÓN DE APLICACIÓN:
   - Cadena de conexión MySQL: 
     mysql://usuario:password@host:3306/yolo_annotator
   - O en formato SQLAlchemy:
     mysql+pymysql://usuario:password@host:3306/yolo_annotator

3. GESTIÓN DE CLASES PERSONALIZADA:
   - Sistema completo de clases por usuario y sesión
   - Clases globales disponibles para todos los usuarios
   - Colores personalizables con validación hexadecimal
   - API REST completa para CRUD de clases
   - Interfaz modal integrada en el anotador

4. STORED PROCEDURES DISPONIBLES:
   - sp_CreateDefaultClasses(user_id, session_name)
   - sp_GetUserClasses(user_id, session_name, include_global)
   - sp_GetClassStatistics(user_id)
   - sp_CleanupExpiredTokens()

5. VISTAS PARA REPORTES:
   - vw_user_statistics: Estadísticas generales de usuarios
   - vw_project_statistics: Estadísticas de proyectos
   - vw_class_stats_by_user: Estadísticas de clases por usuario
   - vw_popular_classes: Clases más utilizadas
   - vw_class_management_summary: Resumen completo de gestión
   - vw_active_sessions: Sesiones activas

6. MANTENIMIENTO AUTOMÁTICO:
   - Limpieza automática de tokens expirados cada hora
   - Actualización de estadísticas diarias
   - Triggers para mantener contadores actualizados

CARACTERÍSTICAS INCLUIDAS:
✅ Sistema completo de autenticación JWT
✅ Gestión personalizada de clases de anotación
✅ Clases globales y específicas por sesión
✅ Todas las tablas necesarias para YOLO annotation
✅ Índices optimizados para performance
✅ Constraints para integridad de datos
✅ Triggers para actualización automática
✅ Stored procedures para operaciones complejas
✅ Vistas para reporting y estadísticas
✅ Eventos para mantenimiento automático
✅ Compatibilidad completa con phpMyAdmin
✅ Datos de ejemplo listos para usar

CREDENCIALES POR DEFECTO:
- Usuario Admin: admin / admin@yolo-annotator.com
- Usuario Test: testuser / test@yolo-annotator.com
- Password por defecto: "password" (cambiar en producción)

PRÓXIMOS PASOS:
1. Ejecutar este script en phpMyAdmin
2. Configurar la aplicación con la nueva cadena de conexión MySQL
3. Crear usuarios específicos para la aplicación
4. Cambiar passwords por defecto
5. Probar la funcionalidad de gestión de clases
6. Configurar backups automáticos
*/
