CREATE DATABASE IF NOT EXISTS todo_app;

USE todo_app;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE todos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text VARCHAR(255) NOT NULL CHECK (text <> ''),
    date DATE,
    time TIME,
    completed BOOLEAN NOT NULL DEFAULT false,
    bookmarked BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_todos_created ON todos(created_at);
CREATE INDEX idx_todos_status ON todos(completed, bookmarked);