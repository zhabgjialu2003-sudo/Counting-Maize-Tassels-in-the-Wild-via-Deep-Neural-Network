-- Maize Detector App — Database Schema
-- MySQL

CREATE TABLE roles (
    role_id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    status ENUM('active','disabled') DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

CREATE TABLE images (
    image_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    image_name VARCHAR(255) NOT NULL,
    image_path VARCHAR(500) NOT NULL,
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE detection_results (
    result_id INT PRIMARY KEY AUTO_INCREMENT,
    image_id INT NOT NULL,
    tassel_count INT NOT NULL DEFAULT 0,
    confidence_score DECIMAL(5,4),
    annotated_image_path VARCHAR(500),
    processing_time DECIMAL(5,2),
    bbox_data JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (image_id) REFERENCES images(image_id)
);

CREATE TABLE reports (
    report_id INT PRIMARY KEY AUTO_INCREMENT,
    report_type ENUM('daily','weekly','monthly') NOT NULL,
    report_date DATE NOT NULL,
    total_uploads INT DEFAULT 0,
    successful_detections INT DEFAULT 0,
    failed_detections INT DEFAULT 0,
    average_tassel_count DECIMAL(6,2),
    chart_data JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE system_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE datasets (
    dataset_id INT PRIMARY KEY AUTO_INCREMENT,
    dataset_name VARCHAR(255) NOT NULL,
    dataset_path VARCHAR(500),
    total_images INT DEFAULT 0,
    annotation_status ENUM('not_started','in_progress','completed') DEFAULT 'not_started',
    annotation_format VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
