# Datasets

Store maize tassel training/evaluation datasets here.  
Large files (>100MB) are excluded from Git via `.gitignore`.

## Required files

| File          | Size  | Source                                                       |
| ------------- | ----- | ------------------------------------------------------------ |
| MTDC-UAV.zip  | 1.3GB | [Dryad](https://doi.org/10.5061/dryad.r2280gbcg) or [OPIA](https://ngdc.cncb.ac.cn/opia/dataset/datasets/tables?dataId=1) |

## Usage

```powershell
python backend/scripts/import_mtdc_demo.py --zip datasets/MTDC-UAV.zip --limit 40
```

The importer copies extracted images to `backend/uploads/mtdc-demo/`.
