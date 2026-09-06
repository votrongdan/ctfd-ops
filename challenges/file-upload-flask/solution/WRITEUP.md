# File Upload Writeup

1. **Objective**: Exploit a file upload vulnerability to achieve Remote Code Execution and read the environment flag.
2. **Vulnerability**: The application takes the `filename` directly from the user's uploaded file and appends it to the upload directory path. There is no sanitization (e.g. `secure_filename`), meaning Path Traversal (`../`) is possible.
3. **Exploitation**:
   - The application serves an `index.html` template.
   - We craft a multipart POST request with the filename set to `../templates/index.html`.
   - The file content is a Jinja2 SSTI payload: `{{ self.__init__.__globals__.__builtins__.__import__('os').environ['FLAG'] }}`.
   - When the server saves the file, it overwrites the original `index.html`.
4. **Flag Retrieval**: Reloading the page parses our injected template, executing the Python code and revealing the flag.
