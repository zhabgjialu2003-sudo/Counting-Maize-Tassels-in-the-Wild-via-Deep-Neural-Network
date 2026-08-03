# Disease model artifacts

This delivery contains the validated model
`maize-disease-20260725-043333`. Its `metadata.json` reports
`deployment_ready: true`; the backend has been verified to load it through the
Unicode-safe TorchScript path.

Model documentation files in this directory:

- `metadata.json`
- `MODEL_CARD.md`
- `SHA256SUMS.json`

The runtime file is stored once at
`models/deployment/maize-disease.torchscript.pt` and is managed by Git LFS.

Supporting files include the model card, training history, pinned-source
manifests, leakage report, and checksums. The Flask disease module remains
unavailable when core files are missing. A future model with
`deployment_ready: false` is rejected unless the server is deliberately started
with `DISEASE_ALLOW_CANDIDATE=true` for evaluation.

The independent YOLO tassel-counting model is stored at
`models/deployment/tassel-best.pt`.
