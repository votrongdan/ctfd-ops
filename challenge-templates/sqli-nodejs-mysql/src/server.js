const express = require('express');
const mysql = require('mysql2/promise');
const path = require('path');

const app = express();
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.urlencoded({ extended: true }));

let pool;

async function initDbPool() {
    pool = mysql.createPool({
        host: 'localhost',
        user: 'root',
        password: '',
        database: 'challenge_db',
        waitForConnections: true,
        connectionLimit: 10,
        queueLimit: 0
    });
}

initDbPool();

app.all('/', async (req, res) => {
    let query = '';
    let results = [];
    let error = '';

    if (req.method === 'POST') {
        query = req.body.query || '';

        // VULNERABLE QUERY
        const sql_query = `SELECT name, description FROM products WHERE name LIKE '%${query}%'`;

        try {
            const [rows] = await pool.query(sql_query);
            results = rows.map(row => [row.name, row.description]);
        } catch (e) {
            error = e.message;
        }
    }

    res.render('index', { query, results, error });
});

app.listen(80, () => {
    console.log('App listening on port 80');
});
