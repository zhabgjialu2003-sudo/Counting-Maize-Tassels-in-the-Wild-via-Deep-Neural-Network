# Agronomist Mobile Photo Selection Design

## Purpose

Restore reliable photo selection on the Agronomist diagnosis page, especially on mobile browsers. Agronomists must be able to take a new leaf photo or choose an existing JPG or PNG image from the device gallery.

## Confirmed Direction

The selected direction is an explicit two-action photo interface consistent with the Farmer upload experience:

- **Take Photo** uses a file input with `accept="image/jpeg,image/png"` and `capture="environment"`.
- **Choose from Gallery** uses a separate file input with the same accepted types and no `capture` attribute.

Both inputs feed one shared selection and preview workflow. They do not create separate diagnosis paths.

## Current Problem

The Agronomist diagnosis view currently renders one file input with `capture="environment"` inside the leaf-photo drop zone. Mobile browsers may force the camera flow or fail to provide a usable gallery choice. This behaviour differs across browsers and prevents Agronomists from reliably selecting an image already stored on the phone.

## Interface Behaviour

The diagnosis view will show two clearly labelled controls close to the existing photo drop zone. On mobile, the controls stack vertically and use full-width touch targets. On wider screens, they may appear side by side.

Choosing a file from either source will:

1. Store the selected file in the existing diagnosis draft state.
2. Replace any previous temporary preview URL safely.
3. Display the selected leaf image in the shared preview area.
4. Display the selected filename in the retained-photo message.
5. Preserve the photo while the user changes language or diagnosis context fields.

Choosing a second photo replaces the first photo consistently regardless of which source was used.

## Component Boundaries

The change is limited to the Agronomist page markup, its inline diagnosis controller, relevant responsive CSS, and focused static/browser tests. The existing disease-diagnosis API, model inference, authentication, database persistence, Farmer pages, and other role pages remain unchanged.

The two file inputs will call one named handler so preview, validation, and draft-state behaviour cannot diverge between camera and gallery sources.

## Error Handling

- Cancelling the operating-system picker leaves the current draft photo unchanged.
- A missing file does not clear the preview or submit a diagnosis.
- The accepted file types remain JPG and PNG.
- Existing API validation remains the final authority for invalid or unsafe image data.
- Preview URL cleanup prevents stale object URLs from accumulating when photos are replaced.
- Human-readable feedback remains available when the user attempts analysis without a selected photo.

## Accessibility

- Each source action has an explicit accessible label.
- Touch targets meet the existing minimum size used by the mobile interface.
- Keyboard users can activate both source actions.
- The controls do not rely on icons alone to communicate their purpose.

## Verification

Automated static tests will confirm that the camera input contains `capture="environment"`, the gallery input does not contain `capture`, both inputs accept JPG and PNG, and both are wired to the shared handler.

Browser verification at a representative mobile viewport will confirm that each visible control opens its corresponding file chooser and that selecting a test image produces the shared preview. A desktop regression check will confirm that the diagnosis form remains readable. The complete project test suite and GitHub repository checks will run before completion.
