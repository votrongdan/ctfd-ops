# IDOR Writeup

1. **Objective**: View the secret note belonging to the admin.
2. **Vulnerability**: The endpoint `/note?id=X` retrieves notes based on the `id` parameter without verifying if the requesting user owns that note.
3. **Exploitation**: The dashboard shows our notes having IDs like 2 or 3. By guessing or enumerating IDs (e.g., `id=1`), we can access the admin's note.
4. **Flag Retrieval**: Navigating to `/note?id=1` displays the secret note and the flag.
