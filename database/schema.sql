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
    permissions JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

CREATE TABLE images (
    image_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    image_name VARCHAR(255) NOT NULL,
    image_path VARCHAR(500) NOT NULL,
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending','processing','completed','failed') DEFAULT 'pending',
    file_size INT,
    access_level VARCHAR(50) DEFAULT 'private',
    preprocessed BOOLEAN NOT NULL DEFAULT FALSE,
    preprocessed_path VARCHAR(500),
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
    quality_status VARCHAR(30) DEFAULT 'unreviewed',
    review_note TEXT,
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

CREATE TABLE image_files (
    file_id INT PRIMARY KEY AUTO_INCREMENT,
    image_id INT NOT NULL,
    file_type VARCHAR(30) NOT NULL CHECK (file_type IN ('original', 'annotated')),
    file_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size INT NOT NULL,
    image_data LONGBLOB NOT NULL,
    encrypted BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_image_file (image_id, file_type),
    FOREIGN KEY (image_id) REFERENCES images(image_id) ON DELETE CASCADE
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

CREATE TABLE access_policies (
    policy_id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    access_level VARCHAR(50) NOT NULL,
    updated_by INT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(user_id)
);

CREATE TABLE fields (
    field_id INT PRIMARY KEY AUTO_INCREMENT,
    field_name VARCHAR(150) NOT NULL,
    location VARCHAR(150) NOT NULL,
    baseline_count INT NOT NULL DEFAULT 0,
    threshold_low INT NOT NULL DEFAULT 0,
    latest_avg_count DECIMAL(8,2) DEFAULT 0,
    health_status VARCHAR(30) DEFAULT 'Healthy',
    anomaly_flag BOOLEAN DEFAULT FALSE,
    anomaly_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE images
    ADD COLUMN field_id INT,
    ADD FOREIGN KEY (field_id) REFERENCES fields(field_id);

CREATE TABLE recommendations (
    recommendation_id INT PRIMARY KEY AUTO_INCREMENT,
    field_id INT NOT NULL,
    user_id INT,
    note TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (field_id) REFERENCES fields(field_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE models (
    model_id INT PRIMARY KEY AUTO_INCREMENT,
    model_name VARCHAR(150) NOT NULL,
    model_version VARCHAR(50) NOT NULL UNIQUE,
    weights_path VARCHAR(500) NOT NULL,
    status ENUM('registered','training','trained','active','archived','failed') DEFAULT 'registered',
    map50 DECIMAL(6,4),
    precision_score DECIMAL(6,4),
    recall_score DECIMAL(6,4),
    iou_threshold DECIMAL(4,2) DEFAULT 0.50,
    parent_model_id INT,
    changelog TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    activated_at DATETIME,
    FOREIGN KEY (parent_model_id) REFERENCES models(model_id)
);

CREATE TABLE training_runs (
    run_id INT PRIMARY KEY AUTO_INCREMENT,
    model_id INT NOT NULL,
    dataset_id INT NOT NULL,
    status ENUM('queued','running','completed','failed') DEFAULT 'queued',
    hyperparameters JSON NOT NULL,
    loss_curve JSON,
    metrics JSON,
    started_at DATETIME,
    completed_at DATETIME,
    error_message TEXT,
    FOREIGN KEY (model_id) REFERENCES models(model_id),
    FOREIGN KEY (dataset_id) REFERENCES datasets(dataset_id)
);
