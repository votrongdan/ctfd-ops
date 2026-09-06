# Example SQLi Writeup

1. **Objective**: Bypass the patient search and extract the hidden flag.
2. **Vulnerability**: The search box (`patient_name`) is vulnerable to SQL injection because it is interpolated into the query directly.
3. **Reconnaissance**: Sending `' ORDER BY 2-- -` works, `' ORDER BY 3-- -` fails. So there are 2 columns.
4. **Table Enumeration**: Payload `' UNION SELECT 1, sql FROM sqlite_master-- -` reveals a table named `secrets` with a `flag` column.
5. **Exploitation**: Sending `a' UNION SELECT 1, flag FROM secrets-- ` will inject the flag into the second column of the output.
6. **Flag Retrieval**: The flag appears in the HTML response under the Diagnosis field.
