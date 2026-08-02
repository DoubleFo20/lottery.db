CREATE DATABASE lottery_ai;

USE lottery_ai;

CREATE TABLE lottery_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    draw_date DATE,
    first_prize VARCHAR(6),
    last2 VARCHAR(2),
    digit1 INT,
    digit2 INT,
    digit3 INT,
    digit4 INT,
    digit5 INT,
    digit6 INT
);

CREATE TABLE predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    draw_date DATE,
    predicted_number VARCHAR(6),
    score FLOAT
);