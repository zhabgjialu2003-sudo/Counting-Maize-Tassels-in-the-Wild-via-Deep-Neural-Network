# Public Assessment Demo Login Design

## Purpose

Make the four fixed assessment accounts visible and easy to use on the public
Render login page. The change is intended for project assessors who need to
enter each role without consulting a separate manual.

## Approved interaction

The existing Quick Demo Access panel will be shown on the public HTTPS login
page when public demo access is explicitly enabled. It contains four role
buttons: Farmer, Researcher, Agronomist, and Admin. Selecting a role fills the
email and shared password fields and moves focus to Sign In. It does not submit
the form automatically, so the assessor remains in control.

The panel uses a two-column grid on wider screens and a single-column layout on
small mobile screens. The shared password is displayed beneath the role cards.
All labels remain in English because this is the common entry page for every
role; the Farmer mobile workspace retains its English/Chinese language control.

## Configuration and data flow

`DEMO_ACCESS_ENABLED` remains the master switch. A new independent environment
flag, `DEMO_ACCESS_ALLOW_PUBLIC`, permits the `/api/demo-access` endpoint to
return credentials for a public hostname only when both flags are true.
Loopback and explicitly enabled private-network behavior remain unchanged.

The password continues to come only from the Render secret
`DEMO_ACCOUNT_PASSWORD`; it must not be committed to source code or
`render.yaml`. The response remains marked `Cache-Control: no-store`. The login
page calls the existing endpoint and renders the existing fixed account list,
so no duplicate credential list is introduced in frontend code.

## Security boundary

Public demo mode intentionally makes the assessment credentials, including the
Admin credential, available to anyone who can open the site. It does not create
new permissions, bypass authentication, or issue a token before Sign In. The
feature must be disabled after the assessment by setting
`DEMO_ACCESS_ALLOW_PUBLIC=false`; existing accounts can then remain available
for manual sign-in without being advertised.

The endpoint must return `{ "enabled": false }` for public hosts unless the new
flag is explicitly true. Authentication rate limits, role checks, audit logs,
session expiry, and PostgreSQL persistence remain unchanged.

## Failure behavior

- Missing or empty `DEMO_ACCOUNT_PASSWORD`: do not expose the panel.
- Master switch disabled: return `enabled: false` for every host.
- Public switch disabled: retain the current public-host denial.
- Endpoint or network failure: leave the normal Sign In and Create Account
  forms usable and keep the Demo panel hidden.

## Verification

Automated tests will cover public denial by default, explicit public opt-in,
the four role records, no-store response headers, and manual-submit frontend
behavior. The full repository suite and GitHub Actions must pass.

After deployment, browser verification will check desktop and 390-pixel mobile
layouts, card-to-form autofill, all four role logins, and the absence of
console errors. The Render health endpoint must remain ready after the change.

## Deployment

`render.yaml` will set `DEMO_ACCESS_ALLOW_PUBLIC=true` for the assessment
deployment. The value is non-secret; the shared password remains a Render
secret. The change will be reviewed through a pull request and deployed only
after GitHub Actions succeeds.
