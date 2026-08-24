<?php
$db = new mysqli('127.0.0.1', 'ctf', 'ctf', 'challenge_db');

if ($db->connect_error) {
    die("Connection failed: " . $db->connect_error);
}

$query = '';
$results = [];
$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $query = $_POST['query'] ?? '';
    
    // VULNERABLE QUERY
    $sql_query = "SELECT name, description FROM products WHERE name LIKE '%{$query}%'";
    
    try {
        $result = $db->query($sql_query);
        if ($result) {
            while ($row = $result->fetch_row()) {
                $results[] = $row;
            }
        } else {
            $error = $db->error;
        }
    } catch (Exception $e) {
        $error = $e->getMessage();
    }
}
?>
<!DOCTYPE html>
<html>
<head>
    <title>Product Search</title>
    <style>
        body { font-family: sans-serif; max-width: 600px; margin: 2rem auto; }
        table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        .error { color: red; font-family: monospace; margin-top: 1rem; }
    </style>
</head>
<body>
    <h1>Product Search</h1>
    <form method="POST" action="/">
        <input type="text" name="query" placeholder="Enter product name" value="<?php echo htmlspecialchars($query); ?>" required>
        <button type="submit">Search</button>
    </form>

    <?php if ($error): ?>
        <div class="error">Error: <?php echo htmlspecialchars($error); ?></div>
    <?php endif; ?>

    <?php if ($query !== ''): ?>
        <table>
            <thead>
                <tr>
                    <th>Product Name</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                <?php if (count($results) > 0): ?>
                    <?php foreach ($results as $row): ?>
                        <tr>
                            <td><?php echo htmlspecialchars($row[0]); ?></td>
                            <td><?php echo htmlspecialchars($row[1]); ?></td>
                        </tr>
                    <?php endforeach; ?>
                <?php else: ?>
                    <tr>
                        <td colspan="2">No results found.</td>
                    </tr>
                <?php endif; ?>
            </tbody>
        </table>
    <?php endif; ?>
</body>
</html>
