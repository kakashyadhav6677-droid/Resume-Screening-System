create database resume_screening;

USE resume_screening;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    role ENUM('employer', 'employee') NOT NULL
);

CREATE TABLE employers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    location VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    gender ENUM('Male', 'Female') DEFAULT NULL,
	website VARCHAR(255),
    company_description TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    resume_path VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT,
    job_id INT,
    application_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
    
CREATE TABLE jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employer_id INT NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    job_description TEXT NOT NULL,
    keywords VARCHAR(255),
    date_posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employer_id) REFERENCES users(id)
);

select * from users;
-- drop table employees;
select * from employers;
select * from employees;
-- delete from users;
describe employees
ALTER TABLE employees
ADD COLUMN cover_letter TEXT,
ADD COLUMN cover_letter_path VARCHAR(255);
select * from applications;
ALTER TABLE applications ADD COLUMN score INT;

update employees set resume_path = '\\uploads' where id = 13;
select id,username,email,role from users;
show databases;