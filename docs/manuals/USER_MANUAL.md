# User Manual

## Start and sign in

1. Start the backend as described in the root README.
2. Open `http://127.0.0.1:5000/frontend/pages/login.html`.
3. Sign in with an account created in PostgreSQL. Seeded accounts are for local
   demonstration only and must not be reused for a public deployment.

The application opens the page allowed for the account role.

## Farmer: count maize tassels

1. Open **Upload**.
2. Select a JPG or PNG maize-field image.
3. Check the preview and submit the image.
4. Wait for upload and inference to finish.
5. Review the tassel count, confidence information and annotated image.
6. Open **History** to revisit stored results.

For useful results, photograph a wide maize-field view with visible tassels,
even lighting and limited motion blur.

## Farmer: use mobile capture

1. Open `/frontend/pages/mobile.html` on the phone.
2. Sign in through the same server origin.
3. Choose the camera or an existing photo.
4. Review the compressed upload size before submission.
5. Keep the page open while mobile data is interrupted; retry when the network
   returns.

The mobile PWA does not change the desktop application. Both interfaces use the
same API and user account.

## Agronomist: screen a maize leaf

1. Open **Agronomist** or the leaf-screening page.
2. Upload a clear close-up image of one affected maize leaf.
3. Add field context if known. A field or plot ID is not required.
4. Submit the image and review its quality status.
5. Read the supported, uncertain, unsupported or retake result.
6. Treat recommendations as screening guidance and inspect the field or request
   expert confirmation when symptoms are severe or unclear.

## Account settings

Open **My Account** to change the display name or login email. Enter the current
password to confirm an email or password change. After a password change, sign
in again with the new password.

## Researcher and Admin functions

Researchers can inspect history, compare registered model metrics, export data
and generate reports. Admins can manage accounts, inspect system status and
review operational records. Server-side authorization prevents a Farmer from
calling these privileged routes.

## Troubleshooting

| Message or symptom | Action |
|---|---|
| Model unavailable | Run `git lfs pull` and restart the backend. |
| PostgreSQL connection failed | Check the local `.env`, service status and database name. |
| Image rejected | Use a real JPG or PNG within the allowed size. |
| Retake requested | Move closer, improve lighting, hold the camera steady and reduce leaf obstruction. |
| Session returns to login | Sign in again; if it repeats, verify the phone uses the same server origin. |
| Upload interrupted | Keep the selected image and retry after connectivity returns. |
