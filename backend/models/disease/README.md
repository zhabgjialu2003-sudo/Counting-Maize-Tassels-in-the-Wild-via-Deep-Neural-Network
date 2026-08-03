# Disease model artifacts

This delivery contains the validated model
`maize-disease-20260725-043333`. Its `metadata.json` reports
`deployment_ready: true`; the backend has been verified to load it through the
Unicode-safe TorchScript path.

Core runtime files:

- `maize_disease.torchscript.pt`
- `metadata.json`
- `MODEL_CARD.md`
- `SHA256SUMS.json`

Supporting files include the model card, training history, pinned-source
manifests, leakage report, and checksums. The Flask disease module remains
unavailable when core files are missing. A future model with
`deployment_ready: false` is rejected unless the server is deliberately started
with `DISEASE_ALLOW_CANDIDATE=true` for evaluation.

Do not rename or replace `backend/models/best.pt`; it is the independent YOLO
tassel-counting model.
