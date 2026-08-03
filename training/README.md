# Training and Evaluation

Training artefacts are separated by task so tassel-counting evidence cannot be
confused with the optional leaf-disease extension.

## Tassel counting

- Source and historical notebooks: [`notebooks/tassel/`](notebooks/tassel/)
- Evaluation outputs should be stored under `results/tassel/` when available.
- The deployable tassel model and provenance are documented under
  [`models/tassel/`](../models/tassel/).

## Disease screening

- Reproducible source notebook:
  [`notebooks/disease/maize_disease_agronomist_training.ipynb`](notebooks/disease/maize_disease_agronomist_training.ipynb)
- Executed evidence notebook:
  [`notebooks/disease/maize_disease_agronomist_training.executed.ipynb`](notebooks/disease/maize_disease_agronomist_training.executed.ipynb)
- Evaluation evidence: [`results/disease/`](results/disease/)
- Deployable model documentation: [`models/disease/`](../models/disease/)

The executed disease notebook contains 16 completed code cells and no stored
error output. Full image datasets are not redistributed here; dataset sources,
pinned revisions, manifests, and licence notes are retained with the experiment
evidence.

