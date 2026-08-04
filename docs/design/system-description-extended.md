# Extended System Description

The system is a bilingual, role-based web and mobile platform for maize tassel counting and cautious maize leaf-condition screening. Its primary agricultural value is to reduce manual tassel counting while giving farmers understandable image-quality feedback and a structured path to Agronomist review. A photo is evidence, not a guarantee: the system separates model output, contextual information, uncertainty, and expert review so that users are not misled by an automated result.

The Farmer workflow supports field-photo upload, tassel count and highlighting, leaf screening, bilingual guidance, result history, and secure email/password maintenance. The Researcher workflow provides governed history, export, dataset retrieval, model comparison, and reproducible evaluation. The Agronomist workflow is field-scoped: only explicitly assigned fields and their evidence are visible, and reviews are recorded as confirmed, corrected, or inconclusive. The Admin workflow manages users, roles, permissions, field assignments, datasets, models, audit logs, backups, and migrations. System controls validate actual content, encrypt image bytes, check model integrity, bound expensive work, and reject stale sessions.

## Human-Centred Design Principles

1. **Explain before instructing.** Results state what the image resembles, how strong the evidence is, and what the user can do next.
2. **Make uncertainty visible.** Low-quality or ambiguous photos lead to retake or confirmation guidance, not false certainty.
3. **Fit field conditions.** Mobile layouts, progress feedback, compressed uploads, and recoverable network errors support 4G/5G use.
4. **Protect dignity and privacy.** Farmers see their own records; Agronomists see only assigned field evidence; Researchers receive governed data; Admin actions are audited.
5. **Keep both languages first-class.** English and Simplified Chinese guidance share stable technical codes but use natural farmer-facing language.

## Architectural Boundaries

- **Boundary layer:** responsive HTML/CSS/JavaScript PWA served from the same HTTPS origin as the API in deployment.
- **Control layer:** Flask route controls, live session validation, image validation, inference controls, advice formatting, field assignment, model governance, rate limiting, migration execution, and background scheduling.
- **Entity layer:** PostgreSQL entities for roles, users, fields, assignments, images, encrypted files, detections, diagnoses, reviews, datasets, models, training runs, reports, migrations, and audit logs.
- **AI layer:** a tassel detector with content/model-aware bounded caching and a separate TorchScript leaf-screening classifier with image-quality and calibrated uncertainty gates.
- **Operations layer:** Waitress bounded threads, configurable trusted roots, environment-based secrets, optional automatic migrations, database readiness, health reporting, backups, and controlled error messages.

## Scope and Limitations

The leaf assistant supports the configured maize classes only and is explicitly not a laboratory diagnosis. Field context improves wording but does not alter raw model evidence. Real-world accuracy depends on representative training data, camera quality, growth stage, geography, and disease prevalence. Public deployment additionally requires managed HTTPS, durable object storage, a shared external rate limiter for horizontal scaling, monitored backups, secret rotation, and agronomic validation of any treatment guidance.
