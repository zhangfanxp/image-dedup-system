CREATE DATABASE IF NOT EXISTS image_dedup
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE image_dedup;

CREATE TABLE IF NOT EXISTS image_library (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    image_name VARCHAR(255),
    image_path VARCHAR(500),
    md5 CHAR(32),
    phash CHAR(16),
    width INT,
    height INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_md5(md5),
    INDEX idx_phash(phash)
);