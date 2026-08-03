# Maize Detector Entity Relationship Diagram

This ERD reflects the implemented PostgreSQL schema and the BCE entities used by
the Farmer, Researcher, Agronomist, Admin, and AI System stories.

```mermaid
erDiagram
    roles ||--o{ users : assigns
    users ||--o{ images : uploads
    users ||--o{ system_logs : creates
    fields ||--o{ images : contains
    images ||--o{ image_files : stores_encrypted
    images ||--o{ detection_results : produces
    fields ||--o{ recommendations : receives
    models ||--o{ training_runs : trains

    roles {
        int role_id PK
        varchar role_name UK
    }
    users {
        int user_id PK
        int role_id FK
        varchar name
        varchar email UK
        varchar password_hash
        enum status
        jsonb permissions
        timestamp created_at
    }
    fields {
        int field_id PK
        varchar field_name
        varchar location
        numeric area_hectares
        varchar crop_stage
        varchar health_status
        boolean anomaly_flag
        text anomaly_reason
    }
    images {
        int image_id PK
        int user_id FK
        int field_id FK
        varchar image_name
        varchar image_path
        enum status
        int file_size
        varchar access_level
        boolean preprocessed
        varchar preprocessed_path
        timestamp upload_time
    }
    image_files {
        int file_id PK
        int image_id FK
        bytea file_data
        varchar mime_type
        boolean encrypted
    }
    detection_results {
        int result_id PK
        int image_id FK
        int tassel_count
        numeric confidence_score
        numeric processing_time
        jsonb bbox_data
        varchar quality_status
        varchar review_status
        text review_note
        timestamp created_at
    }
    recommendations {
        int recommendation_id PK
        int field_id FK
        varchar category
        varchar priority
        text recommendation_text
        timestamp created_at
    }
    models {
        int model_id PK
        varchar model_name
        varchar version
        varchar weight_path
        enum status
        numeric precision_score
        numeric recall_score
        numeric map50
        numeric map50_95
        timestamp created_at
    }
    training_runs {
        int run_id PK
        int model_id FK
        enum status
        jsonb parameters
        jsonb metrics
        timestamp started_at
        timestamp completed_at
    }
    datasets {
        int dataset_id PK
        varchar dataset_name
        varchar dataset_path
        int total_images
        enum annotation_status
        varchar annotation_format
        timestamp created_at
    }
    reports {
        int report_id PK
        enum report_type
        date report_date
        int total_uploads
        int successful_detections
        int failed_detections
        numeric average_tassel_count
        jsonb chart_data
    }
    system_logs {
        int log_id PK
        int user_id FK
        varchar action
        text details
        timestamp created_at
    }
    access_policies {
        int policy_id PK
        varchar role_name UK
        jsonb permissions
        timestamp updated_at
    }
```

`database/migrations/001_user_story_compliance.sql` upgrades an existing installation
without deleting its data. `database/schema/schema_postgresql.sql` creates a clean
installation. Uploaded image bytes are encrypted before disk/database storage;
the `encrypted` flag records that storage contract.
