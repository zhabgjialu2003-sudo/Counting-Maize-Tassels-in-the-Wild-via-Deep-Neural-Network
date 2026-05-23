# Maize Detector -- Week 10 Entity Relationship Diagram (ERD)

This ERD follows the revised Week 10 checklist's seven main database tables:
`users`, `roles`, `images`, `detection_results`, `reports`, `system_logs`, and `datasets`.

```mermaid
erDiagram
    roles ||--o{ users : assigns
    users ||--o{ images : uploads
    images ||--o{ detection_results : produces
    detection_results }o--o{ reports : summarized_in
    users ||--o{ system_logs : creates
    users }o--o{ datasets : manages_or_accesses

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
        enum status
        timestamp created_at
    }

    images {
        int image_id PK
        int user_id FK
        varchar image_name
        varchar image_path
        timestamp upload_time
        enum status
        int file_size
        varchar access_level
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
        enum report_type
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
        enum annotation_status
        varchar annotation_format
        timestamp created_at
    }
```

Notes:
- `users.status`: active / disabled
- `images.status`: pending / processing / completed / failed
- `reports.report_type`: daily / weekly / monthly
- `datasets.annotation_status`: not_started / in_progress / completed
- The `reports` and `datasets` links show project-level business relationships. The Week 10 SQL schema keeps these tables independent without explicit foreign keys.
