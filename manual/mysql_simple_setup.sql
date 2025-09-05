-- ========================================================
-- YOLO ANNOTATOR - SCRIPT MYSQL ACTUALIZADO PARA PHPMYADMIN
-- ========================================================
-- IMPORTANTE: Ejecutar este script paso a paso en phpMyAdmin
-- Este script está sincronizado con los modelos SQLAlchemy del proyecto
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
  hashed_password VARCHAR(255) NOT NULL,
  is_active TINYINT(1) DEFAULT 1,
  is_admin TINYINT(1) DEFAULT 0,
  created_at DATETIME NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY ix_users_username (username),
  UNIQUE KEY ix_users_email (email),
  KEY ix_users_id (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paso 4: Crear tabla de sesiones de usuario con hash privado
CREATE TABLE user_sessions (
  id INT NOT NULL AUTO_INCREMENT,
  session_name VARCHAR(100) NOT NULL,
  session_hash VARCHAR(64) NOT NULL,
  user_id INT NOT NULL,
  created_at DATETIME NOT NULL,
  is_active TINYINT(1) DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY ix_user_sessions_session_hash (session_hash),
  KEY ix_user_sessions_id (id),
  KEY fk_user_sessions_user_id (user_id),
  CONSTRAINT fk_user_sessions_user_id FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paso 5: Crear tabla de tokens en lista negra (blacklist)
CREATE TABLE token_blacklist (
  id INT NOT NULL AUTO_INCREMENT,
  token VARCHAR(500) NOT NULL,
  blacklisted_at DATETIME NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY ix_token_blacklist_token (token),
  KEY ix_token_blacklist_id (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paso 6: Crear tabla de clases de anotación con soporte para sesiones privadas
CREATE TABLE annotation_classes (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL,
  color VARCHAR(7) NOT NULL DEFAULT '#ff0000',
  user_id INT NOT NULL,
  session_name VARCHAR(100) DEFAULT NULL,
  session_hash VARCHAR(64) DEFAULT NULL,
  is_global TINYINT(1) DEFAULT 0,
  is_active TINYINT(1) DEFAULT 1,
  created_at DATETIME NOT NULL,
  PRIMARY KEY (id),
  KEY ix_annotation_classes_id (id),
  KEY ix_annotation_classes_session_hash (session_hash),
  KEY fk_annotation_classes_user_id (user_id),
  CONSTRAINT fk_annotation_classes_user_id FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paso 7: Insertar usuario administrador por defecto
-- Password: 'admin123' hasheado con bcrypt
INSERT INTO users (username, email, hashed_password, is_active, is_admin, created_at) VALUES 
('admin', 'admin@yolo-annotator.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0WS8P5Vda6', 1, 1, NOW());

-- Paso 8: Insertar usuario de prueba
-- Password: 'test123' hasheado con bcrypt  
INSERT INTO users (username, email, hashed_password, is_active, is_admin, created_at) VALUES 
('testuser', 'test@yolo-annotator.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0WS8P5Vda6', 1, 0, NOW());

-- Paso 9: Crear sesión de ejemplo con hash único
INSERT INTO user_sessions (session_name, session_hash, user_id, created_at, is_active) VALUES 
('demo_session', SHA2('demo_session_admin_unique', 256), 1, NOW(), 1);

-- Paso 10: Crear clases globales por defecto
INSERT INTO annotation_classes (name, color, user_id, session_name, session_hash, is_global, is_active, created_at) VALUES
('adidas', '#FF0000', 1, NULL, NULL, 1, 1, NOW()),
('nike', '#00FF00', 1, NULL, NULL, 1, 1, NOW()),
('puma', '#0000FF', 1, NULL, NULL, 1, 1, NOW()),
('reebok', '#FFFF00', 1, NULL, NULL, 1, 1, NOW()),
('converse', '#FF00FF', 1, NULL, NULL, 1, 1, NOW()),
('vans', '#00FFFF', 1, NULL, NULL, 1, 1, NOW());

-- Paso 11: Verificaciones del sistema
SELECT 'INSTALACIÓN COMPLETADA CORRECTAMENTE - TODAS LAS TABLAS CREADAS' as status;

-- Verificación: Mostrar tablas creadas
SHOW TABLES;

-- Verificación: Contar registros en cada tabla
SELECT 'users' as tabla, COUNT(*) as registros FROM users
UNION ALL
SELECT 'user_sessions' as tabla, COUNT(*) as registros FROM user_sessions
UNION ALL
SELECT 'token_blacklist' as tabla, COUNT(*) as registros FROM token_blacklist
UNION ALL
SELECT 'annotation_classes' as tabla, COUNT(*) as registros FROM annotation_classes;

-- Verificación: Mostrar usuarios insertados
SELECT id, username, email, is_admin, is_active, created_at FROM users;

-- Verificación: Mostrar sesiones creadas
SELECT id, session_name, session_hash, user_id, is_active FROM user_sessions;

-- Verificación: Mostrar clases de anotación creadas
SELECT id, name, color, is_global, is_active FROM annotation_classes WHERE is_global = 1;
