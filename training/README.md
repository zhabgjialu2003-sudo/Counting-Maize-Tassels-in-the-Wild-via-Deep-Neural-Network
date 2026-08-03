# Maize Disease Training Record

This folder preserves the reproducible training code and the real outputs used
by the Agronomist feature. It is evidence of the experiment, not a replacement
for professional field diagnosis.

## What the photo contributes

The image model looks for visible leaf evidence of four supported outcomes:
healthy appearance, common rust, gray leaf spot, and northern corn leaf blight.
The farmer does not need to know a field or plot ID before uploading. Optional
field context improves the practical advice, while low-confidence or unfamiliar
images are rejected instead of being forced into a disease class.

## Notebooks

- `notebooks/maize_disease_agronomist_training.ipynb`: clean source notebook
  intended for a fresh top-to-bottom run.
- `notebooks/maize_disease_agronomist_training.executed.ipynb`: completed run
  with all cell outputs retained. All 16 code cells completed and no error
  output is stored.

## Recorded evaluation

| Evaluation set | Samples | Accuracy | Macro F1 | Accepted accuracy | Coverage |
|---|---:|---:|---:|---:|---:|
| Internal test | 794 | 96.85% | 95.70% | 99.61% | 63.85% |
| External field test | 523 | 98.47% | 95.46% | 99.77% | 83.75% |
| PlantDoc field audit | 14 | 71.43% | 69.44% | 87.50% | 57.14% |
| CDS field test | 509 | 99.21% | 99.31% | 100.00% | 84.48% |

The PlantDoc result is advisory because only 14 supported samples were
available. The recorded out-of-distribution false-acceptance rate is 8.63%.
Full thresholds, confidence intervals, dataset revisions, and deployment gates
are stored in `results/metadata.json`.

## Result files

- `results/training_curves.png`: loss and validation trend.
- `results/*confusion_matrix.png`: internal and independent field evaluations.
- `results/training_history.csv`: epoch-level training history.
- `results/partition_manifest.csv`: reproducible train/calibration/test split.
- `results/leakage_removals.csv`: duplicate-removal audit.
- `results/cds_manifest.json` and `results/plantdoc_file_map.csv`: external data
  traceability records.
- `results/MODEL_CARD.md`, `results/metadata.json`, and
  `results/SHA256SUMS.json`: model scope, metrics, gates, and checksums.

The image datasets themselves are not redistributed in this repository. The
notebook pins the public data sources and revisions so another team member can
download them under the applicable licences and reproduce the experiment.

## Deployment link

The exported production model is stored once at
`backend/models/disease/maize_disease.torchscript.pt` and is loaded by
`backend/disease_inference.py`. Its SHA-256 is:

```text
4F48A440E2EB35BEF220107F9E777F9A3A10DC8FA0B79E0296A022CBA700EF17
```

This hash exactly matches the TorchScript artefact produced by the recorded
training run. Large `.pt` files are managed through Git LFS.

## Re-run

1. Open the source notebook in Google Colab or Kaggle.
2. Select a T4 GPU runtime.
3. Run every cell from top to bottom without skipping the data-leakage checks,
   calibration, external tests, or export-equivalence test.
4. Compare the new artefact hashes and metrics before replacing the deployed
   model.

A full run downloads public datasets and requires substantial GPU time. Do not
run only the export cell: a replacement model should pass leakage checks,
calibration, independent evaluation, deployment gates, and export equivalence.
