CREATE DATABASE IF NOT EXISTS challenge_db;
USE challenge_db;

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE flag_store (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flag VARCHAR(255) NOT NULL
);

INSERT INTO products (name, description) VALUES 
('Quantum Analyzer', 'Examine quantum states.'),
('Aether Engine', 'Clean renewable engine.'),
('Chrono Pocket Watch', 'Perceive time slower.'),
('Cyber Deck v9', 'Neural link terminal.'),
('Nanite Repair Kit', 'Repairs micro-fractures.');
