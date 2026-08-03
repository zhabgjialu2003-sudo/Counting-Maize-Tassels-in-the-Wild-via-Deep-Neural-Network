# Verified Test Results

Verification date: 2026-08-03 (Asia/Shanghai)

## Summary

| Check | Result |
|---|---|
| Automated test suite | 54 passed, 0 failed |
| PostgreSQL-backed API tests | Passed |
| Tassel deployment model | Loaded and completed real inference |
| Disease deployment model | Loaded, ready and completed real inference |
| API health endpoint | HTTP 200, service status `ok` |
| Executed disease notebook | 16 executed code cells, 0 error outputs |
| Entry-point links and repository structure | Passed |
| Current guidance language | English-only check passed |
| Sensitive-file tracking check | Passed |

The automated suite was run with:

```powershell
python -m unittest discover -s tests -v
```

The PostgreSQL password was supplied only to the local process environment. It
was not written to a tracked file.

## Real inference smoke test

### Tassel counting

- Input: `examples/tassel-counting/input/DJI_0243 (2).JPG`
- Model: `models/deployment/tassel-best.pt`
- Mode: fast
- Detected tassels: 123
- Mean detection confidence: 0.4595
- Processing time on the validation computer: 1.318 seconds

This confirms that the deployment weights can be materialized through Git LFS,
loaded by Ultralytics, and used through the repository inference wrapper.

### Disease screening

- Local validation input: `test_images/test1.JPG` from the uncommitted test
  archive supplied for validation
- Model: `models/deployment/maize-disease.torchscript.pt`
- Model version: `maize-disease-20260725-043333`
- Health: ready and deployment-ready
- Screening outcome: unsupported
- Highest candidate: common rust at 0.536851 confidence

The unsupported result is correct safety behaviour for an image that does not
pass the calibrated acceptance thresholds: the application must request better
or more suitable evidence instead of presenting a low-confidence disease label
as fact. The local image is not committed because redistribution rights have not
been established.

## Model integrity

| Model | SHA-256 |
|---|---|
| `tassel-best.pt` | `37bca6b8e817d911424dbd22f720f9cbe00248036e0fc6305ef853f8b38d9913` |
| `maize-disease.torchscript.pt` | `4f48a440e2eb35bef220107f9e777f9a3a10dc8fa0b79e0296a022cba700ef17` |

Automated checks reject missing model files, Git LFS pointer stubs, and hash
mismatches. These checks make a fresh clone failure visible before a demo.

## Scope and interpretation

The smoke test proves that both runtime models load and execute and that the API,
database, repository contracts, mobile static contracts, authorization rules,
account management and human-centred rejection paths pass the automated suite.
It does not replace the evaluation metrics, confidence intervals and dataset
limitations recorded under `training/results/disease/` and `models/`.
