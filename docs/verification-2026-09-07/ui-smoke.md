# UI smoke test — updated 2026-09-08

## Follow-up: simple smoke completed

Restarted only the isolated Gunicorn test server with 2 workers x 16 threads. The player challenge list loaded successfully afterward. No product code changes were needed during this smoke test.

- Player challenge list/detail: opened UI Single HTTP and UI Multi HTTP TCP.
- Single HTTP: launched successfully, displayed an HTTP URL and remaining time, then destroyed successfully.
- Multi-port HTTP+TCP: launched successfully; showed separate URLs for 8080 and 8081 (second hostname includes `-p8081`) and `nc 127.0.0.1 19101`.
- Connected to exactly the TCP port displayed on UI using a socket from the host, received the instance flag, submitted it through the browser form, and saw **Correct**.
- Destroyed the multi-port instance, created it again, and observed a new instance UUID/URLs and TCP port 19100. Destroyed the replacement successfully afterward.
- Block mode: saved through admin UI. Two cookie sessions were separated using localhost and 127.0.0.1 in the same browser. Second login for the same player displayed **This account is already logged in on another device**. After logout in the first session, second-session login succeeded.
- Restored Monitoring mode through UI; Settings saved displayed.
- Sampled error console logs in the final two tabs returned no errors.

Remaining limits: browser blocked the test nip.io HTTP URL with ERR_BLOCKED_BY_CLIENT, so HTTP destination content was not verified in this UI run (HTTP routing was covered by earlier integration tests). Logout redirects to `/`, which returned 404 in the disposable test database; authentication logout itself worked, demonstrated by the next successful Block-mode login. No homepage fixture was added for this smoke test. No cross-browser/exhaustive checks, downloaded Word content inspection, or repeat automated regression was run because no product code changed. The earlier partial-run notes below are retained as history, not the final completion status.

Target: isolated final-code server at localhost:19080, MariaDB/Redis test database. Used Codex in-app browser, real forms and clicks. Production stack was not restarted or modified.

## Verified through UI

- Admin login (`ui-admin`): redirected to challenges with Admin Panel link.
- Challenge list as admin: both `UI Single HTTP` and `UI Multi HTTP TCP` visible.
- Provisioning: uploaded a one-row CSV using browser file chooser; preview showed Total 1, Valid 1, Invalid 0; confirmed the dialog; Results showed Successfully created 1 accounts.
- Credential download: clicked Word download link and received the browser download event. Did not independently verify that the final file was saved to disk or inspect its contents in Word.
- Player login: account created by the provisioning UI successfully logged in and received Profile/Settings/Logout navigation.
- Session monitoring: admin session was present with timestamps; repeated live API requests returned HTTP 200.

## Incomplete / blocked

- Player challenge list remained at its loading indicator. Browser navigation/focus commands repeatedly timed out when using additional tabs. No console errors were returned by the sampled browser log call, but that does not prove absence of frontend errors.
- The test server was launched with 2 workers x 2 threads. Long-lived notification/SSE connections are a suspected capacity issue, not a confirmed root cause. A proposed restart with more threads was not completed: the stop command failed because the container lacks the `kill` executable, and the subsequent launch permission was rejected. No product code was changed on this hypothesis.
- Not yet verified in UI: player logout, Block mode in two sessions, challenge detail, instance create/destroy/recreate, per-user flags, single/multi-port access, HTTP+TCP, displayed URL/port correctness.
- Earlier automated regression results remain separate evidence; they are not counted as completion of these UI steps.

Temporary fixtures remain in the isolated DB: ui-admin, ui-player, smoke_browser_player_ui001 and the two UI challenges. Setup helper is /tmp/ctfd-fix-env/app/ui_smoke_setup.py; test CSV is /tmp/ui-smoke-players.csv. Gunicorn test server is still running with the original thread configuration. Credentials are intentionally omitted from this report.
