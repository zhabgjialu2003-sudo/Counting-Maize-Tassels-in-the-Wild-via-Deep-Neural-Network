# Render Public Deployment Design

## Purpose

Deploy the complete Maize Detector application to a stable public HTTPS URL for final-project assessment. The hosted system must support authenticated Farmer, Researcher, Agronomist, and Admin workflows, maize tassel detection, maize leaf screening, result review, and PostgreSQL-backed records. GitHub Pages remains the marketing website and links to the live system.

## Selected Approach

Use one Render native Python web service and one Render-managed PostgreSQL database in the Singapore region. The web service uses the Standard 2 GB instance type, and the database uses the smallest paid PostgreSQL instance suitable for the assessment period.

This design was selected over a Docker deployment because the application already has a compatible Python entry point and requirements file. A native build avoids maintaining a large container image while still allowing an explicit CPU-only PyTorch installation. A split static-frontend/API design was rejected because it would add cross-origin configuration, two deployment lifecycles, and more failure points without improving the assessment workflow.

## Architecture

- Render Web Service: serves the Flask API, desktop interface, mobile interface, and both AI inference workflows from one origin.
- Render PostgreSQL: stores users, roles, fields, uploaded image blobs, detection results, disease reviews, reports, model records, and audit data.
- GitHub repository: provides the source revision, deployment configuration, database schema, migrations, and Git LFS metadata.
- GitHub Pages: remains the public marketing site and provides a link to the Render application.
- Render-managed TLS: provides the public `onrender.com` HTTPS endpoint; no paid domain is required.

The web service and database are placed in the Singapore region so their private connection remains within one Render region and latency is appropriate for the expected users.

## Build and Model Artifacts

The build installs Python 3.11 dependencies and CPU-only PyTorch packages. OpenCV uses the headless package because the server does not require a desktop display stack.

Both deployment models are required:

- `models/deployment/tassel-best.pt`
- `models/deployment/maize-disease.torchscript.pt`

The build verifies that each file is a materialised model rather than a Git LFS pointer and checks its known SHA-256 digest. If Render's source checkout does not materialise an LFS object, a repository-owned build helper downloads the corresponding public Git LFS object and verifies it before installation completes. A checksum mismatch stops the deployment.

## Database Initialisation

A deployment helper connects through Render-provided PostgreSQL environment variables. It performs the following idempotent sequence:

1. Detect whether the base `users` table exists.
2. Apply `database/schema/schema_postgresql.sql` only for an empty database.
3. Apply all non-destructive versioned migrations.
4. Check migration checksums.
5. Provision or refresh the four fixed assessment accounts.

The base schema is never reapplied to an existing application database, preventing accidental data loss during redeployment.

## Authentication and Public Access

The public site requires normal email-and-password authentication. The login page may display the four assessment email addresses, but public one-click authentication is disabled. The assessment password is supplied as a Render secret and is not committed to GitHub.

The production configuration includes:

- generated Flask signing and file-encryption secrets;
- HTTPS-aware secure response headers;
- same-origin CORS settings;
- query-string authentication disabled;
- bounded upload sizes and validated JPG/PNG decoding;
- request rate limits already implemented by the application;
- local-only development credentials disabled;
- PostgreSQL available only through Render's private service connection.

## Runtime and Data Flow

1. A user opens the Render HTTPS URL and signs in.
2. The browser uploads a maize-field or close-up leaf image to the same-origin Flask API.
3. The backend validates the image format, dimensions, MIME type, and byte limit.
4. The relevant CPU inference model processes the image.
5. PostgreSQL stores the user-visible result, provenance, bounding boxes or disease-screening output, and encrypted image data.
6. The API returns the result to the desktop or mobile interface.

Temporary local files may use Render's ephemeral filesystem during processing. Durable assessment records and image blobs remain in PostgreSQL, so a web-service restart does not remove them.

## Availability and Operations

- Service plan: Standard, 2 GB RAM and 1 CPU.
- Database plan: smallest paid Render PostgreSQL configuration.
- Region: Singapore for both resources.
- Health check: `/api/health`.
- Instance count: one, because CPU inference is guarded and the assessment workload is low-volume.
- Automatic deployment: disabled for the first release. It can be enabled after end-to-end verification.
- Background backups: application filesystem backups are disabled in hosted mode because the filesystem is ephemeral; database durability is handled by Render PostgreSQL.

The expected baseline cost is approximately USD 31 per month before optional storage or excess bandwidth. The resources should remain active for at least one month after the final presentation.

## Error Handling

- Missing or invalid model artifacts fail the build before traffic is accepted.
- Database initialisation failures stop the pre-deploy step.
- Failure to connect to PostgreSQL stops application startup.
- Failure to load the tassel model stops application startup.
- Unsupported or uncertain leaf images return the existing user-facing retake or uncertainty guidance rather than a fabricated diagnosis.
- Invalid uploads return bounded 4xx responses without persisting incomplete records.
- The health endpoint is used by Render to reject an unhealthy release.

## Verification Plan

Before deployment:

- validate the Render Blueprint syntax;
- run the complete automated test suite;
- check Python, JavaScript, and deployment-script syntax;
- verify both model checksums;
- scan tracked deployment files for committed secrets;
- confirm the base schema is not reapplied to an existing database.

After deployment:

- confirm the Render release is live and `/api/health` returns HTTP 200;
- inspect startup and error logs;
- sign in with each of the four assessment roles;
- run one tassel-counting upload and one leaf-screening upload;
- confirm results remain accessible after a service restart;
- verify desktop and mobile layouts over the public HTTPS URL;
- add the verified live-system URL to GitHub Pages and the project documentation.

## Rollback

Keep the last known-good Render release available for rollback. Database changes remain forward-only and idempotent. If the first public deployment fails, do not expose a partially working URL; correct the build or configuration, redeploy, and repeat the full smoke test before adding the link to GitHub Pages.

## Acceptance Criteria

- A public `https://*.onrender.com` URL serves the application.
- The health endpoint reports a ready database and both deployed model states.
- All four fixed assessment accounts can authenticate with the supplied password.
- Public one-click Demo Access is unavailable.
- Farmer tassel counting and leaf screening complete with persisted results.
- Researcher, Agronomist, and Admin protected pages enforce their roles.
- No database password, application secret, or encryption key is present in Git history.
- The service remains available for the required one-month assessment window.
