# SSTI Writeup

1. **Objective**: Perform Server-Side Template Injection to read the environment variables containing the flag.
2. **Vulnerability**: The user input in the `name` parameter is formatted directly into an HTML string which is then evaluated by `render_template_string()`.
3. **Exploitation**: We can use Jinja2 syntax `{{ ... }}` to execute python code.
   A classic python jail escape payload allows us to import the `os` module:
   `{{ self.__init__.__globals__.__builtins__.__import__('os').environ['FLAG'] }}`
4. **Flag Retrieval**: Sending the payload in a POST request returns the flag rendered directly in the HTML response.
