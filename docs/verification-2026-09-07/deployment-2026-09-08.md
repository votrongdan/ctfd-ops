# Production deployment — 2026-09-08

Deployed code commit: `b097be9` on `main`.
Target: existing Compose container `ctfd-ctfd-1`, served at http://localhost through `ctfd-nginx-1`.
The application bind-mounts this repository's `CTFd` directory read-only. Existing image already contained the required dependencies. Only the CTFd application container was stopped/started; MariaDB, Redis, nginx and FRP were not restarted.

## Backup

Private directory outside the repository:
`/home/dan/Desktop/ctfd-whale1-backups/20260908-predeploy-b097be9/`

- `code-before.tar.gz`: parent of the deployment commit.
- `database.sql`: full ctfd SQL dump, refreshed while CTFd was stopped; dump completion marker checked.
- `redis.rdb`: Redis SAVE snapshot taken while CTFd was stopped.
- `config-uploads.tar.gz`: existing config, Compose file and uploads; archive validated.
- `deployment-secret.key`: newly persisted CTFd cookie secret.
- `provisioning.key`: newly generated provisioning encryption key, copied after successful CSV preview.

No persistent cookie secret existed in the original container environment, config or mount. CTFd's read-only source mount prevented saving its generated secret, so restart invalidates the former cookies. A 64-byte secret was created at `CTFd/.ctfd_secret_key` (Git-ignored), with a read ACL for container UID 1001. This makes future restarts retain the same secret. Existing users need to sign in again after this deployment; their accounts are unchanged. Do not delete either persistent key during upgrades or rollback.

## Verified after restart

- Startup and plugin migrations completed; Gunicorn is running with the existing production gevent configuration.
- Browser admin login using the provided existing account succeeded.
- Challenge list displayed the existing challenges.
- CSV upload/preview returned 1 valid row; Cancel removed the preview without creating any account.
- Session monitoring showed the admin session.
- Existing `Example SQLi - Hospital` challenge: launched an admin-owned Whale instance through UI, received success and access URL; HTTP request through FRP port 8001 with that hostname returned 200 and the hospital page; destroyed the instance through UI successfully.
- Final database counts: **15 users, 10 challenges, 0 Whale containers, 0 provisioning jobs**. User/challenge counts match pre-deployment counts.
- `ssm_sessions.lifecycle`, `ssm_sessions.pending_until` and `account_provisioning_jobs` exist.
- Persistent cookie secret is readable by the application; provisioning key creation and encryption were exercised by preview.
- Final container state: running, restart count 0. No ERROR/Traceback/HTTP 500 matched the final five-minute application log check.

The earlier test-suite and UI smoke reports provide broader regression evidence. Production smoke did not create test player accounts or rerun every multi-port/Block/download scenario. No push to a remote repository was performed.

## Rollback

For a code regression, stop the CTFd application container, run `git revert b097be9`, then start the application container. Keep the cookie secret, provisioning key, uploads and additive database columns/tables. Reverting application code does not restore the database; do not automatically restore the old dump because it would discard activity after deployment. The prior code does not need the added columns removed.

Use the pre-deployment SQL/Redis backup only for a separately planned full-state recovery while application writes are stopped. Restoring the old Redis snapshot does not resurrect cookies signed by the original ephemeral secret. The code archive is an additional recovery source, not a reason to overwrite current user data.
