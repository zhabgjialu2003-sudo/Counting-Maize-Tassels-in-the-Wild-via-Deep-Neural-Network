# Mobile Photo Source Design

## Objective

Allow mobile users to deliberately take a new photo or select an existing JPG or PNG image from their phone gallery on both the tassel-counting and leaf-health pages.

## User Experience

Each mobile upload form presents two clearly labelled controls:

- **Take photo** opens the rear-facing camera when the browser supports camera capture.
- **Choose from gallery** opens the device file or photo picker and does not request camera capture.

Both controls feed the same existing preview, validation, compression, upload, and analysis workflow. Selecting an image through either source replaces the current selection. Desktop upload behaviour remains unchanged.

## Implementation Boundaries

- Add a camera-specific file input with `capture="environment"`.
- Add a gallery-specific file input without a `capture` attribute.
- Keep `accept="image/jpeg,image/png"` on both inputs.
- Route both input change events to the existing image-selection handler.
- Preserve all current API contracts, authentication, image limits, analysis behaviour, and result rendering.
- Provide English and Simplified Chinese labels through the existing mobile language mechanism where the page already supports bilingual copy.
- Keep buttons large, high contrast, and touch-friendly.

## Error Handling

Cancellation leaves the existing selection unchanged. Invalid formats, oversized images, decoding errors, network errors, and API errors continue to use the existing messages and recovery flow.

## Verification

- Static tests confirm that each mobile workflow has one camera input with `capture="environment"` and one gallery input without `capture`.
- Existing frontend and backend tests remain green.
- Browser testing in a mobile viewport confirms that both controls are visible and that a gallery-selected image reaches the existing preview and upload workflow.
- Desktop viewport testing confirms that the existing desktop upload control is unchanged.

## Out of Scope

This change does not add native-device permissions, alter image analysis models, change storage policy, or redesign the surrounding pages.
