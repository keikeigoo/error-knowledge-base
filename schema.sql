CREATE DATABASE IF NOT EXISTS error_knowledge_base_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE error_knowledge_base_db;

CREATE TABLE IF NOT EXISTS errors (
    id INT PRIMARY KEY AUTO_INCREMENT,
    error_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    situation VARCHAR(1000) NOT NULL,
    solution VARCHAR(2000) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
