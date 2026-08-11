# Local Demo Login Design

## Objective

Make the four project roles quick to demonstrate from the login page without publishing an administrator password to public visitors or committing a usable password to Git.

## User Experience

When local demo access is enabled, the sign-in panel shows a compact **Quick Demo Access** section below the normal Sign In button. It contains a responsive two-by-two set of role buttons:

- Farmer — `john@farm.com`
- Researcher — `liwei@research.org`
- Agronomist — `maria@agro.com`
- Admin — `admin@system.com`

The shared local demo password is displayed once below the buttons. Selecting a role fills the existing Email and Password fields and places focus on Sign In. It does not submit the form or sign in automatically. On narrow screens the buttons use one column.

The section is absent when demo access is disabled or when the request arrives through a non-local host. Normal sign-in and Farmer account creation remain unchanged.

## Security Boundary

The static login page and tracked repository files must not contain a working plaintext password.

An unauthenticated configuration endpoint returns `{ "enabled": false }` unless all of the following are true:

1. local demo access is explicitly enabled by environment configuration;
2. a demo password is configured outside Git; and
3. the request host is `localhost`, `127.0.0.1`, or `[::1]`; alternatively, an
   explicit private-network flag may allow an RFC 1918 or private IPv6 address
   for a controlled same-Wi-Fi mobile demonstration.

Only when all checks pass may the endpoint return the four fixed demo identities and the configured shared password. Public hostnames and production deployments cannot expose the credentials even if they reach the same development server. Private-network access remains disabled by default and must be explicitly enabled for a controlled mobile demonstration.

The tracked `.env.example` documents disabled defaults but contains no working demo password. The local `backend/.env` may enable the feature and store the agreed shared demo password; that file remains ignored by Git.

## Account Provisioning

An explicit local setup command activates or creates the four fixed demo identities, hashes the configured shared password using the existing password-hashing mechanism, and assigns the correct role. It never runs automatically during application startup.

The setup command fails safely when demo access is disabled, the password is missing, the password violates policy, or a required role is unavailable. The implementation will run the command against the current local database and verify that each identity authenticates as its intended role.

## Components and Data Flow

1. The login page requests demo-access configuration from the backend after loading.
2. A disabled response leaves the Demo section hidden.
3. An enabled local response is rendered with DOM APIs and fixed role styling.
4. Clicking a role copies that account's email and shared password into the existing fields.
5. The existing `handleLogin` function remains the only path that submits credentials and performs role-based routing.

## Error Handling

Failure to load Demo configuration is silent and leaves the normal login form fully usable. No error message should suggest that Demo accounts exist on a production deployment. Account setup uses a transaction so a provisioning failure cannot leave only some roles updated.

## Verification

- Unit tests cover disabled defaults, missing configuration, local-host access, opt-in private-network access, and rejection through public hosts.
- Frontend tests verify the compact role controls, manual-submit behaviour, and absence of hard-coded credentials.
- API login checks verify Farmer, Researcher, Agronomist, and Admin accounts with the local shared password.
- Browser testing checks desktop and mobile layouts, field filling, manual Sign In, and role routing.
- The complete repository test suite and GitHub Actions must pass.

## Out of Scope

This feature does not bypass authentication, weaken role authorization, create production default credentials, or provide one-click automatic login.
