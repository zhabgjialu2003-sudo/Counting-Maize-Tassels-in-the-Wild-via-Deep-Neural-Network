# Security Policy

## Reporting a vulnerability

Do not disclose a vulnerability through a public issue if it could expose
credentials, private images, user records, model artefacts, or database access.
Contact the repository owner through the GitHub profile associated with
[`zhabgjialu2003-sudo`](https://github.com/zhabgjialu2003-sudo) and include:

- the affected route, component, or file;
- steps to reproduce the problem with non-sensitive test data;
- the potential impact; and
- a suggested mitigation, if known.

Please allow reasonable time for investigation before public disclosure.

## Supported code

Security fixes target the current `main` branch. Historical coursework under
`coursework/` is retained as assessment evidence and is not a supported release.

## Secret and data handling

- Store PostgreSQL credentials, `SECRET_KEY`, and `FILE_ENCRYPTION_KEY` only in
  local or deployment environment variables.
- Never commit `.env`, database backups, farmer uploads, tokens, or private
  datasets.
- Never publish shared demo credentials. Configure the first administrator with
  `python -m backend.scripts.bootstrap_admin` and assign passwords individually.
- Treat uploaded field and leaf images as private unless explicit permission
  says otherwise.
- Keep model and dataset paths within their configured approved roots.
- Verify deployment model hashes before activation.
- Use the protected image endpoints; never expose filesystem paths in an API.

If a secret is committed, revoke or rotate it immediately. Removing it from the
latest file is not sufficient because Git history may still contain the value.
