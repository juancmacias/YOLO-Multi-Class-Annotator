-- ========================================================
-- YOLO ANNOTATOR - SCRIPT MYSQL SIMPLIFICADO PARA PHPMYADMIN
-- ========================================================
-- IMPORTANTE: Ejecutar este script paso a paso en phpMyAdmin
-- ========================================================

-- Paso 1: Crear la base de datos
CREATE DATABASE IF NOT EXISTS yolo_annotator DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Paso 2: Seleccionar la base de datos
USE yolo_annotator;

-- Paso 3: Crear tabla de usuarios
CREATE TABLE users (
  id INT NOT NULL AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL,
  email VARCHAR(100) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_active TINYINT(1) DEFAULT 1,
  is_admin TINYINT(1) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  last_login TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_username (username),
  UNIQUE KEY uk_users_email (email),
  KEY idx_users_is_active (is_active),
  KEY idx_users_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paso 4: Crear tabla de tokens JWT
CREATE TABLE user_tokens (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  token_hash VARCHAR(255) NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_revoked TINYINT(1) DEFAULT 0,
  PRIMARY KEY (id),
  KEY fk_user_tokens_user_id (user_id),
  KEY idx_user_tokens_expires_at (expires_at),
  KEY idx_user_tokens_token_hash (token_hash),
  CONSTRAINT fk_user_tokens_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paso 5: Crear tabla de proyectos
CREATE TABLE projects (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  user_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_active TINYINT(1) DEFAULT 1,
  PRIMARY KEY (id),
  KEY fk_projects_user_id (user_id),
  KEY idx_projects_is_active (is_active),
  KEY idx_projects_created_at (created_at),
  CONSTRAINT fk_projects_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paso 6: Crear tabla de sesiones de usuario
CREATE TABLE user_sessions (
  id INT NOT NULL AUTO_INCREMENT,
  session_name VARCHAR(100) NOT NULL,
  user_id INT NOT NULL,
  project_id INT DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_active TINYINT(1) DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_sessions_name_user (session_name, user_id),
  KEY fk_user_sessions_user_id (user_id),
  KEY fk_user_sessions_project_id (project_id),
  KEY idx_user_sessions_is_active (is_active),
  CONSTRAINT fk_user_sessions_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT fk_user_sessions_project_id FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paso 7: Crear tabla de clases de anotación (NUEVA FUNCIONALIDAD)
CREATE TABLE annotation_classes (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  project_id INT DEFAULT NULL,
  name VARCHAR(50) NOT NULL,
  color VARCHAR(7) NOT NULL DEFAULT '#FF0000',
  session_name VARCHAR(100) DEFAULT NULL,
  is_global TINYINT(1) DEFAULT 0,
  is_active TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_annotation_classes_user_session_name (user_id, session_name, name),
  KEY fk_annotation_classes_user_id (user_id),
  KEY fk_annotation_classes_project_id (project_id),
  KEY idx_annotation_classes_session_name (session_name),
  KEY idx_annotation_classes_is_active (is_active),
  KEY idx_annotation_classes_is_global (is_global),
  KEY idx_annotation_classes_created_at (created_at),
  KEY idx_annotation_classes_user_session_active (user_id, session_name, is_active),
  CONSTRAINT fk_annotation_classes_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT fk_annotation_classes_project_id FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paso 8: Crear tabla de imágenes
CREATE TABLE images (
  id INT NOT NULL AUTO_INCREMENT,
  filename VARCHAR(255) NOT NULL,
  original_filename VARCHAR(255) NOT NULL,
  file_path VARCHAR(500) NOT NULL,
  file_size BIGINT DEFAULT NULL,
  width INT DEFAULT NULL,
  height INT DEFAULT NULL,
  user_id INT NOT NULL,
  project_id INT DEFAULT NULL,
  session_name VARCHAR(100) DEFAULT NULL,
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_annotated TINYINT(1) DEFAULT 0,
  annotation_count INT DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uk_images_filename_user (filename, user_id),
  KEY fk_images_user_id (user_id),
  KEY fk_images_project_id (project_id),
  KEY idx_images_session_name (session_name),
  KEY idx_images_uploaded_at (uploaded_at),
  KEY idx_images_is_annotated (is_annotated),
  CONSTRAINT fk_images_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT fk_images_project_id FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paso 9: Crear tabla de anotaciones
CREATE TABLE annotations (
  id INT NOT NULL AUTO_INCREMENT,
  image_id INT NOT NULL,
  user_id INT NOT NULL,
  class_id INT DEFAULT NULL,
  class_name VARCHAR(50) NOT NULL,
  x_center DECIMAL(10,8) NOT NULL,
  y_center DECIMAL(10,8) NOT NULL,
  width DECIMAL(10,8) NOT NULL,
  height DECIMAL(10,8) NOT NULL,
  confidence DECIMAL(5,4) DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY fk_annotations_image_id (image_id),
  KEY fk_annotations_user_id (user_id),
  KEY fk_annotations_class_id (class_id),
  KEY idx_annotations_class_name (class_name),
  KEY idx_annotations_created_at (created_at),
  CONSTRAINT fk_annotations_image_id FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE,
  CONSTRAINT fk_annotations_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT fk_annotations_class_id FOREIGN KEY (class_id) REFERENCES annotation_classes (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paso 10: Crear tabla de log de actividades
CREATE TABLE activity_log (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  action VARCHAR(50) NOT NULL,
  resource_type VARCHAR(50) NOT NULL,
  resource_id INT DEFAULT NULL,
  details JSON DEFAULT NULL,
  ip_address VARCHAR(45) DEFAULT NULL,
  user_agent TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY fk_activity_log_user_id (user_id),
  KEY idx_activity_log_action (action),
  KEY idx_activity_log_resource_type (resource_type),
  KEY idx_activity_log_created_at (created_at),
  CONSTRAINT fk_activity_log_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paso 11: Insertar datos de ejemplo
INSERT INTO users (username, email, password_hash, is_active, is_admin) VALUES 
('admin', 'admin@yolo-annotator.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0WS8P5Vda6', 1, 1),
('testuser', 'test@yolo-annotator.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0WS8P5Vda6', 1, 0);

-- Paso 12: Crear proyecto de ejemplo
INSERT INTO projects (name, description, user_id) VALUES 
('Proyecto Demo', 'Proyecto de demostración para YOLO Annotator', 1);

-- Paso 13: Crear sesión de ejemplo
INSERT INTO user_sessions (session_name, user_id, project_id) VALUES 
('demo_session', 1, 1);

-- Paso 14: Crear clases globales por defecto
INSERT INTO annotation_classes (user_id, project_id, name, color, session_name, is_global, is_active) VALUES
(1, NULL, 'person', '#FF0000', NULL, 1, 1),
(1, NULL, 'vehicle', '#00FF00', NULL, 1, 1),
(1, NULL, 'animal', '#0000FF', NULL, 1, 1),
(1, NULL, 'object', '#FFFF00', NULL, 1, 1);

-- Paso 15: Mensaje de confirmación
SELECT 'INSTALACIÓN COMPLETADA CORRECTAMENTE' as status;

-- Verificación: Mostrar tablas creadas
SHOW TABLES;

-- Verificación: Mostrar usuarios insertados
SELECT id, username, email, is_admin FROM users;

-- Verificación: Mostrar clases creadas
SELECT id, name, color, is_global FROM annotation_classes;
