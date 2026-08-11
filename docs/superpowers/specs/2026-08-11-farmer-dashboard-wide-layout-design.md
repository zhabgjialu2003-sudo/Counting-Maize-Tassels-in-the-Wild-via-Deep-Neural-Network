# Farmer Dashboard Wide-Layout Design

## Purpose

Correct the Farmer dashboard presentation on desktop displays so that it uses the available browser width naturally. The change must preserve the existing agricultural visual identity, dashboard functions, authentication flow, data, and mobile experience.

## Confirmed Direction

The selected direction is **Option A: Balanced full-width**. On desktop screens, the navigation spans the viewport and the main workspace uses a responsive content width of up to approximately 1,440 pixels with comfortable side margins. On smaller screens, the existing single-column mobile layout remains in effect.

## Problem Diagnosis

The supplied screenshot shows the document scrollbar near the centre of a 2K display. This indicates that the page was opened in an automated browser context with an approximately 1,024-pixel fixed viewport while the browser window occupied a much wider area. The current shared `.container` rule also caps content at 1,100 pixels, which makes dashboard content unnecessarily narrow on wide desktop displays.

The repair therefore covers both presentation conditions:

1. Open the project in a normal Chrome browser window for manual use and demonstrations, without the fixed automation viewport.
2. Improve the desktop dashboard container so its cards and results table use wide screens more effectively.

## Layout Behaviour

### Desktop

- The top navigation spans the full document viewport.
- The main Farmer workspace is centred and may grow to approximately 1,440 pixels.
- Page gutters remain visible and scale safely on narrower laptops.
- The three task cards remain in one row when adequate space is available.
- The four statistics remain readable in a balanced row.
- The recent-results table receives the additional width instead of leaving a large unused region.

### Tablet and Mobile

- Existing responsive breakpoints remain authoritative.
- Task and statistic cards collapse according to the current responsive rules.
- The dedicated Farmer mobile page and bottom navigation are not redesigned.
- No horizontal document scrolling is introduced.

## Implementation Boundary

The change is limited to shared layout styling where safe and a dashboard-specific width rule where necessary. No API endpoint, database schema, account, model, upload workflow, disease analysis, or navigation destination will change.

The implementation must avoid widening form-oriented pages such as login, profile, and leaf-health workflows beyond their intended reading widths. If the shared `.container` rule affects those pages, the wider maximum will be scoped to the Farmer dashboard rather than applied globally.

## Accessibility and Resilience

- Text contrast and existing focus behaviour remain unchanged or improve.
- Content remains usable at browser zoom levels above 100%.
- Long image names remain contained within the recent-results table.
- A wide viewport must not reduce tap-target size or mobile readability.
- Layout changes use CSS and do not depend on JavaScript, network state, or API success.

## Verification

The completed layout will be checked at these representative viewport widths:

- 1,366 pixels: common laptop desktop layout.
- 1,920 pixels: wide desktop and presentation layout.
- 390 pixels: mobile layout regression check.

Verification will confirm that the navigation spans the viewport, dashboard content is centred and appropriately wide, no horizontal scrollbar appears, all dashboard cards remain readable, the recent-results table remains usable, and mobile behaviour is unchanged. Existing automated tests will also be run in proportion to the CSS-only risk.
