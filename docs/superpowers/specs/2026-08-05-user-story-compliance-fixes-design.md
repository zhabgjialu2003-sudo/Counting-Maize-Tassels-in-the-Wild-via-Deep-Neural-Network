# User Story Compliance Fixes Design

Date: 2026-08-05

## Objective

Close the remaining implementation and verification gaps identified by the
CodeGraph audit without changing the approved user-story wording or breaking
existing frontend, API, database, or mobile behavior.

The implementation quality target is production-oriented: minimal duplication,
clear helper boundaries, deterministic migrations, stable API contracts,
actionable errors, direct acceptance tests, and documentation that accurately
matches the final code. Improvements remain scoped to the maize-tassel and
leaf-screening project requirements.

The work covers four related gaps:

1. B.4 and D.9 model comparison must enforce the same artifact and dataset
   trust boundaries as B.9 evaluation.
2. A.11 upload retries must not create duplicate image records after a network
   interruption.
3. B.7 result provenance must be complete while internal storage paths remain
   private.
4. High-risk success paths need direct automated acceptance evidence.

## Design Decisions

### 1. Shared model-evaluation trust boundary

Model comparison and single-model evaluation will use one shared validation
helper. The helper will:

- resolve the registered model only from approved model roots;
- verify the recorded artifact SHA-256 when present;
- resolve dataset YAML only from configured dataset roots;
- return safe validation errors without exposing absolute paths;
- run evaluation only after both resources pass validation.

Stored-metric comparison remains available when no dataset YAML is supplied.
It will be labelled `stored-evaluation`; it must not imply that two artifacts
were executed. A shared validation run is allowed only when both registered
artifacts are present and verified.

### 2. Idempotent field uploads

The frontend will generate a random idempotency key for each deliberate file
selection and reuse that key when the same selection is retried. Selecting or
clearing a file creates a new upload intent.

The upload API will accept the key in an `Idempotency-Key` request header. The
database will store the key with the owning user and enforce uniqueness on the
pair `(user_id, upload_idempotency_key)`. This prevents cross-user collisions.

Server behavior:

- first request: validate, encrypt, persist, and return `201`;
- repeated completed request: return the existing image identity with `200` and
  `idempotent_replay: true`;
- repeated request while the first is incomplete: return a controlled conflict
  response that asks the client to retry;
- requests without the header remain supported for backward compatibility and
  continue using UUID storage names.

The key does not replace content SHA-256. The digest remains scientific and
storage provenance; the key represents one user action.

### 3. Safe, complete result provenance

Detection results will persist and return:

- registered `model_id` and `model_version` where available;
- `inference_mode` (`fast` or `accurate`);
- confidence and quality/review state;
- a stable public image identity suitable for protected retrieval.

API responses will stop exposing `image_path`, `original_image_path`,
`annotated_image_path`, and registered `weights_path`. Existing frontend code
will use protected image endpoints derived from `image_id` and `result_id`.

Compatibility aliases for count and confidence remain unchanged.

### 4. Database migration

A new numbered, non-destructive migration will add:

- `images.upload_idempotency_key`;
- `detection_results.model_id` when not already present;
- `detection_results.model_version`;
- `detection_results.inference_mode`;
- a partial unique index on `(user_id, upload_idempotency_key)` for non-null
  keys;
- a foreign key from detection results to models where compatible with the
  existing schema.

The canonical schema file will be updated to match the migration. Existing
rows remain valid with nullable provenance fields.

## Error Handling

- Validation errors use stable, user-readable messages and 4xx responses.
- Absolute filesystem paths and raw exception text never enter public JSON.
- Idempotent replay never creates a second encrypted blob or image row.
- A failed first upload does not permanently consume its idempotency key.
- Missing or unverifiable model artifacts return a controlled 409 response.
- Missing evaluation runtime returns 503 without falling back to fabricated
  metrics.

## Testing Strategy

### Required regression tests

- B.4 rejects an artifact outside approved roots.
- B.4 rejects an artifact whose recorded digest does not match.
- B.4 rejects an unapproved dataset YAML.
- B.4 executes a shared validation only after both resources pass validation.
- A.11 repeated requests with the same user/key return one image row and one
  encrypted file.
- A.11 different users may use the same key without collision.
- A.11 a new selection/key creates a new image record.
- B.7 result JSON includes safe provenance and contains no internal paths.
- Existing Farmer result and annotated-image views continue to work.

### Additional success-path evidence

Add focused tests for dataset manifest export, successful report persistence,
Agronomist review persistence, preprocessing, model evaluation persistence,
and deployment validation using isolated fixtures or mocks at external-runtime
boundaries. Real destructive restore and long-running training remain separate
manual acceptance tests, while their validation, queuing, and failure behavior
stay automated.

### Completion gate

- all existing tests pass;
- all new tests pass;
- CodeGraph shows no unvalidated path from B.4 to model evaluation;
- CodeGraph shows upload replay converging on one Image entity;
- public result payloads contain no storage or weight paths;
- repository documentation remains English-only;
- the working tree contains no secrets or generated runtime data.
- modified Python and JavaScript paths contain no duplicate validation logic
  that can drift between endpoints;
- migrations are safe to discover and apply repeatedly;
- new tests cover authorization, success, replay, rejection, and persistence;
- comments explain security invariants rather than restating the code.

## Scope Exclusions

- No user-story text, BCE diagrams, sequence diagrams, or Word deliverables are
  rewritten during this implementation.
- No authentication architecture migration is included.
- No real production backup restore or long-running model training is executed
  automatically.
- No unrelated frontend redesign or backend refactor is included.
