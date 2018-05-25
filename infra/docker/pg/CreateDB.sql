CREATE TABLE posts (
    id serial PRIMARY KEY,
    date_time TEXT NOT NULL,
    post_data TEXT NOT NULL,
    votes INTEGER NOT NULL
);

