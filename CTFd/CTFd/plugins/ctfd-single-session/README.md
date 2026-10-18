# CTFd Single Session Monitor Plugin

This plugin for CTFd allows administrators to monitor and restrict user accounts to a single concurrent active session, preventing account sharing during a CTF competition.

## Features

*   **Monitoring Mode**: By default, multiple concurrent sessions are allowed, but the plugin records these events. Administrators can view a log of multiple session events to identify potential account sharing without impacting the player's experience.
*   **Block Mode**: Restricts users to only one active session at a time. If a user logs into an account on a second device while their session on the first device is still active, the new login attempt will be rejected.
*   **Admin Dashboard**: A dedicated dashboard for administrators to:
    *   View all currently active user sessions (with IP and User-Agent details).
    *   Review and resolve security events (e.g., multiple session detections, blocked logins).
    *   Manually force-logout specific sessions or all sessions for a user.
*   **Race-Condition Safe**: Uses database-level locks (e.g., `SELECT FOR UPDATE`) to handle simultaneous login attempts securely (on supported databases like MySQL/PostgreSQL).

## Installation

The plugin is included in [ctfd-ops](https://github.com/votrongdan/ctfd-ops) at `CTFd/CTFd/plugins/ctfd-single-session/`.

1.  To install it in another CTFd instance, clone `ctfd-ops` and copy the plugin folder into that instance's `CTFd/plugins` directory:
    ```bash
    git clone https://github.com/votrongdan/ctfd-ops.git
    cp -r ctfd-ops/CTFd/CTFd/plugins/ctfd-single-session /path/to/CTFd/CTFd/plugins/
    ```
2.  Restart your CTFd instance for the plugin to be loaded.

## Configuration

Administrators can configure the plugin via the CTFd Admin Interface by navigating to the **Whale/Plugins** dropdown (or directly through the Admin Menu if registered there), or going to `/plugins/ctfd-single-session/admin/settings`.

*   **Operational Mode**: Choose between Monitoring Mode (default) and Block Mode. Switching to Block Mode will apply immediately to new login attempts.
*   **Event Cooldown**: Time in seconds to suppress duplicate event generation for a user. Default is 300 seconds (5 minutes).
*   **Heartbeat Interval**: Frequency in seconds of how often the "last seen" timestamp is updated for a session. Default is 30 seconds.
*   **Track IP Addresses**: Toggle whether to record the IP address associated with a session.
*   **Track User Agent**: Toggle whether to record the browser User-Agent associated with a session.

## Architecture & Compatibility

This plugin avoids relying on Python global state and instead tracks active sessions using a combination of CTFd's cache (Redis or Filesystem) and a custom database table (`ssm_sessions`). This makes it fully compatible with multi-worker architectures like Gunicorn.

API tokens are excluded from session monitoring, as they trigger the login flow on every request and are not interactive browser sessions.
