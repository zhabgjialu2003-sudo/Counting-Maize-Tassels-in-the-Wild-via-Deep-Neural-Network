# Maize Disease Training Record / 玉米叶片病害训练记录

This folder preserves the reproducible training code and the real outputs used
by the Agronomist feature. It is evidence of the experiment, not a replacement
for professional field diagnosis.

本文件夹保存 Agronomist 功能所使用的可复现训练代码和真实运行结果。它既方便老师
检查，也方便组员重新运行；模型只提供田间初筛建议，不能替代农艺师的现场诊断。

## What the photo contributes / 上传照片的作用

The image model looks for visible leaf evidence of four supported outcomes:
healthy appearance, common rust, gray leaf spot, and northern corn leaf blight.
The farmer does not need to know a field or plot ID before uploading. Optional
field context improves the practical advice, while low-confidence or unfamiliar
images are rejected instead of being forced into a disease class.

模型会从叶片照片中寻找四类可见证据：未见明确支持病害、普通锈病、灰斑病和玉米
大斑病。农民即使不知道地块编号，也可以直接上传照片；地块信息只用于补充更贴近
实际的建议。当照片模糊、拍摄对象不合适或证据不足时，系统会提示无法可靠判断，
而不是强行给出病名。

## Notebooks / Notebook 说明

- `notebooks/maize_disease_agronomist_training.ipynb`: clean source notebook
  intended for a fresh top-to-bottom run.
- `notebooks/maize_disease_agronomist_training.executed.ipynb`: the completed
  run with all cell outputs retained. All 16 code cells completed and no error
  output is stored.

- `notebooks/maize_disease_agronomist_training.ipynb`：用于重新训练的干净源码。
- `notebooks/maize_disease_agronomist_training.executed.ipynb`：保留真实输出的执行版；
  16 个代码单元均已完成，未保存任何报错。

## Recorded evaluation / 已记录的评估结果

| Evaluation set | Samples | Accuracy | Macro F1 | Accepted accuracy | Coverage |
|---|---:|---:|---:|---:|---:|
| Internal test | 794 | 96.85% | 95.70% | 99.61% | 63.85% |
| External field test | 523 | 98.47% | 95.46% | 99.77% | 83.75% |
| PlantDoc field audit | 14 | 71.43% | 69.44% | 87.50% | 57.14% |
| CDS field test | 509 | 99.21% | 99.31% | 100.00% | 84.48% |

The PlantDoc result is advisory because only 14 supported samples were
available. The recorded out-of-distribution false-acceptance rate is 8.63%.
Full precision, thresholds, confidence intervals, dataset revisions, and all
deployment gates are in `results/metadata.json`.

PlantDoc 只有 14 张符合当前类别定义的样本，因此该结果只作为补充观察，不把小样本
成绩夸大为确定结论。记录的分布外图片误接收率为 8.63%。完整阈值、置信区间、
数据版本和部署门槛见 `results/metadata.json`。

## Result files / 结果文件

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
download them legally and reproduce the experiment.

本仓库不重复分发图片数据集。Notebook 已固定公开数据来源及版本，组员可按原许可下载
并复现实验。

## Deployment link / 与项目的连接

The exported production model is stored once at
`backend/models/disease/maize_disease.torchscript.pt` and is loaded by
`backend/disease_inference.py`. Its SHA-256 is:

```text
4F48A440E2EB35BEF220107F9E777F9A3A10DC8FA0B79E0296A022CBA700EF17
```

This hash exactly matches the TorchScript artifact produced by the recorded
training run. Large `.pt` files are managed through Git LFS.

部署模型只保存一份，由 `backend/disease_inference.py` 直接加载；上面的哈希值与训练
输出完全一致，证明 GitHub 中的训练结果和项目实际使用的模型是同一个文件。

## Re-run / 重新运行

1. Open the source notebook in Google Colab or Kaggle.
2. Select a T4 GPU runtime.
3. Run every cell from top to bottom without skipping the data leakage checks,
   calibration, external tests, or export-equivalence test.
4. Compare the new artifact hashes and metrics before replacing the deployed
   model.

重新训练会下载公开数据集，并需要较长时间和 GPU。不要只运行最后的导出单元；只有
完整通过数据泄漏检查、校准、独立测试和导出一致性测试的模型，才适合接入项目。
