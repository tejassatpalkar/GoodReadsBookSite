CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    isbn VARCHAR(10) NOT NULL,
    title VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    year INTEGER NOT NULL CHECK (year > 0)
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL,
    hash VARCHAR NOT NULL
);

CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    comment VARCHAR NOT NULL,
    rating DECIMAL(3, 2) NOT NULL CHECK (rating <= 5 and rating >= 0),
    time TIMESTAMP NOT NULL
);
