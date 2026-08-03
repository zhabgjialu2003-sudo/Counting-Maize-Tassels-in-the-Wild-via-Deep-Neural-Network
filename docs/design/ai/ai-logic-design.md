# AI Logic Design

## Tassel-counting pipeline

1. Decode the uploaded maize-field image.
2. Correct image orientation and normalize colour data.
3. Use direct YOLO inference for suitable images.
4. Split large images into overlapping tiles when the configured path requires
   field-scale processing.
5. Transform tile detections into full-image coordinates.
6. Merge duplicate boxes with intersection-over-union non-maximum suppression.
7. Return the tassel count, boxes, confidence values, processing time and an
   annotated result.

The deployed file is `models/deployment/tassel-best.pt`. Its provenance and
hash are recorded in `models/tassel/MODEL_PROVENANCE.md`.

## Disease-screening pipeline

1. Decode a JPG or PNG and reject unsafe dimensions or invalid image bytes.
2. Measure size, brightness, contrast and blur.
3. Request a new photo when quality is inadequate.
4. Resize, centre-crop and normalize the image with the training metadata.
5. Run the EfficientNet V2-S TorchScript model.
6. Apply temperature calibration to the logits.
7. Evaluate confidence, probability margin and normalized entropy.
8. Return `supported`, `uncertain`, `unsupported`, or `retake_required`.
9. Convert the technical result into practical, language-appropriate advice.

The disease model supports healthy appearance, common rust, gray leaf spot and
northern corn leaf blight. It deliberately rejects unfamiliar or weak evidence
instead of assigning every photo to a disease class.

## Separation of concerns

- Inference modules return technical evidence and stable response contracts.
- The advice engine owns user-facing interpretation.
- Flask routes own authorization, persistence and review workflows.
- Metadata owns class order, calibration and acceptance thresholds.
- Training notebooks own acquisition, leakage checks, calibration, evaluation
  and export evidence.

## Evaluation safeguards

- Development, calibration and untouched test partitions are distinct.
- Image hashes are checked to remove cross-partition duplicates.
- Internal, external field, PlantDoc and CDS evaluations are reported
  separately.
- Small-sample PlantDoc evidence is labelled advisory.
- Out-of-distribution false acceptance is measured and gated.
- TorchScript export equivalence is checked before deployment.

## Known limitations

- Tassel visibility changes with growth stage, occlusion and camera viewpoint.
- Disease classes do not cover every maize condition or nutrient deficiency.
- Field advice depends on image evidence and optional context; it is not a
  laboratory confirmation.
- Model metrics describe recorded datasets and do not guarantee identical
  performance in every farm, country or device camera.
