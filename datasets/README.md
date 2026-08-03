# Datasets

This directory documents external training and evaluation datasets. Full image
datasets are not committed. Keep original raw data unchanged and record every
cleaning, class mapping, split and duplicate-removal decision in the associated
training evidence.

## Tassel-counting data

| File          | Size  | Source                                                       |
| ------------- | ----- | ------------------------------------------------------------ |
| MTDC-UAV.zip  | 1.3GB | [Dryad](https://doi.org/10.5061/dryad.r2280gbcg) or [OPIA](https://ngdc.cncb.ac.cn/opia/dataset/datasets/tables?dataId=1) |

## Usage

```powershell
python backend/scripts/import_mtdc_demo.py --zip datasets/MTDC-UAV.zip --limit 40
```

The importer copies extracted images to `backend/uploads/mtdc-demo/`.

## Disease-screening data

The disease notebook pins and documents:

- PlantVillage for development and internal evaluation;
- PlantDoc under CC BY 4.0 for an advisory field-image audit;
- the CDS field dataset for independent evaluation.

Exact source revisions, licence notes, split manifests and duplicate-removal
records are stored in `training/results/disease/metadata.json` and its companion
manifests. Verify the applicable licence before redistributing any source image.
