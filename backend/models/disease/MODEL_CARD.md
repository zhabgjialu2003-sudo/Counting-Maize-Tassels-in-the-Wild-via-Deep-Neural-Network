# Maize Leaf Disease Assistant Model Card

## Intended use

Image-assisted screening for four maize leaf conditions. This model is not a
confirmed field diagnosis and must not prescribe pesticide products or dosage.

## Status

- Model version: `maize-disease-20260725-043333`
- Architecture: `efficientnet_v2_s`
- Deployment ready: **True**
- External field samples: 523
- External field macro-F1: 0.9546
- PlantDoc field macro-F1: 0.6944
- PlantDoc supported images: 14 (advisory audit only)
- PlantDoc accepted accuracy: 0.8750
- PlantDoc accepted coverage: 0.5714
- CD&S field macro-F1: 0.9931
- Accepted external accuracy: 0.9977
- Accepted external coverage: 0.8375
- OOD false-acceptance rate: 0.0863

## Important limitations

- PlantDoc contributes only 14 unambiguous supported
  test images, so it is disclosed as an advisory challenge audit rather than an
  independent deployment gate.
- The public external maize test sources have no healthy maize field class.
- CD&S field images were collected at a Purdue research site; PlantDoc images
  were web-sourced. Neither source substitutes for project-region field data.
- Performance may change by country, hybrid, growth stage, camera, weather, and
  farming practice.
- Unsupported diseases, insect damage, nutrient stress, and chemical injury can
  resemble supported classes.
- Continue collecting independent, labelled project field images and retain
  agronomist review decisions for future evaluation.

## Quality gates

```json
{
  "external_macro_f1_at_least_0_80": true,
  "cds_macro_f1_at_least_0_80": true,
  "supported_class_recall_at_least_0_70": true,
  "cds_class_recall_at_least_0_70": true,
  "accepted_external_accuracy_at_least_0_90": true,
  "accepted_external_coverage_at_least_0_30": true,
  "ood_false_acceptance_at_most_0_10": true,
  "external_ece_at_most_0_08": true,
  "cds_ece_at_most_0_10": true,
  "no_cross_partition_hash_leakage": true,
  "external_sample_count_at_least_20": true,
  "torchscript_equivalence": true
}
```

## Advisory audits

```json
{
  "plantdoc_supported_samples": 14,
  "plantdoc_advisory_only_because_supported_samples_below_20": true,
  "plantdoc_accepted_accuracy": 0.875,
  "plantdoc_accepted_coverage": 0.5714285714285714
}
```
