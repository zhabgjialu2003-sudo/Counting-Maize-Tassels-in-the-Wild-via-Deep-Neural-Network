# Maize Detector -- Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    roles ||--o{ users : "role_id"
    users ||--o{ images : "user_id"
    users ||--o{ system_logs : "user_id"
    images ||--o{ detection_results : "image_id"
    images ||--|{ image_files : "image_id"

    roles {
        int role_id PK
        varchar role_name
    }

    users {
        int user_id PK
        varchar name
        varchar email UK
        varchar password_hash
        int role_id FK
        enum status "active|disabled"
        timestamp created_at
    }

    images {
        int image_id PK
        int user_id FK
        varchar image_name
        varchar image_path
        timestamp upload_time
        enum status "pending|processing|completed|failed"
        int file_size
        varchar access_level
    }

    image_files {
        int file_id PK
        int image_id FK_UK "UNIQUE(image_id,file_type)"
        varchar file_type "original|annotated"
        varchar file_name
        varchar mime_type
        int file_size
        bytea image_data
        timestamp created_at
    }

    detection_results {
        int result_id PK
        int image_id FK
        int tassel_count
        numeric confidence_score
        varchar annotated_image_path
        numeric processing_time
        jsonb bbox_data
        timestamp created_at
    }

    reports {
        int report_id PK
        enum report_type "daily|weekly|monthly"
        date report_date
        int total_uploads
        int successful_detections
        int failed_detections
        numeric average_tassel_count
        jsonb chart_data
        timestamp created_at
    }

    system_logs {
        int log_id PK
        int user_id FK
        varchar action
        text details
        timestamp created_at
    }

    datasets {
        int dataset_id PK
        varchar dataset_name
        varchar dataset_path
        int total_images
        enum annotation_status "not_started|in_progress|completed"
        varchar annotation_format
        timestamp created_at
    }
```
