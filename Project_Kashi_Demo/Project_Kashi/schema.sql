CREATE DATABASE IF NOT EXISTS project_kashi CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE project_kashi;

SET FOREIGN_KEY_CHECKS = 0;
DROP VIEW IF EXISTS vw_account_details;
DROP PROCEDURE IF EXISTS sp_customer_account_summary;
DROP FUNCTION IF EXISTS fn_account_balance;
DROP TRIGGER IF EXISTS trg_transaction_after_insert;
DROP TABLE IF EXISTS loan_payment;
DROP TABLE IF EXISTS loan;
DROP TABLE IF EXISTS bank_transaction;
DROP TABLE IF EXISTS account_holder;
DROP TABLE IF EXISTS account;
DROP TABLE IF EXISTS employee;
DROP TABLE IF EXISTS branch;
DROP TABLE IF EXISTS customer;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE customer (
  customer_id INT AUTO_INCREMENT PRIMARY KEY,
  first_name VARCHAR(60) NOT NULL,
  last_name VARCHAR(60) NOT NULL,
  date_of_birth DATE NULL,
  gender ENUM('Female','Male','Other','Prefer not to say') NULL,
  mobile VARCHAR(20) NOT NULL,
  email VARCHAR(120) NULL UNIQUE,
  address VARCHAR(255) NULL,
  city VARCHAR(80) NULL,
  registration_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_customer_mobile (mobile)
);

CREATE TABLE branch (
  branch_id INT AUTO_INCREMENT PRIMARY KEY,
  branch_name VARCHAR(100) NOT NULL,
  ifsc_code VARCHAR(20) NOT NULL UNIQUE,
  address VARCHAR(255) NOT NULL,
  city VARCHAR(80) NOT NULL,
  state VARCHAR(80) NOT NULL,
  contact_number VARCHAR(20) NULL
);

CREATE TABLE employee (
  employee_id INT AUTO_INCREMENT PRIMARY KEY,
  employee_name VARCHAR(120) NOT NULL,
  mobile VARCHAR(20) NOT NULL,
  email VARCHAR(120) NULL UNIQUE,
  designation VARCHAR(80) NOT NULL,
  salary DECIMAL(12,2) NOT NULL DEFAULT 0 CHECK (salary >= 0),
  joining_date DATE NOT NULL,
  branch_id INT NOT NULL,
  CONSTRAINT fk_employee_branch FOREIGN KEY (branch_id) REFERENCES branch(branch_id)
);

CREATE TABLE account (
  account_id INT AUTO_INCREMENT PRIMARY KEY,
  account_number VARCHAR(30) NOT NULL UNIQUE,
  account_type ENUM('Saving','Current','Salary') NOT NULL,
  opening_date DATE NOT NULL,
  balance DECIMAL(14,2) NOT NULL DEFAULT 0 CHECK (balance >= 0),
  status ENUM('Active','Inactive','Closed') NOT NULL DEFAULT 'Active',
  branch_id INT NOT NULL,
  CONSTRAINT fk_account_branch FOREIGN KEY (branch_id) REFERENCES branch(branch_id)
);

CREATE TABLE account_holder (
  customer_id INT NOT NULL,
  account_id INT NOT NULL,
  holder_since DATE NOT NULL,
  holder_type ENUM('Primary','Joint') NOT NULL DEFAULT 'Primary',
  PRIMARY KEY (customer_id, account_id),
  CONSTRAINT fk_holder_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
  CONSTRAINT fk_holder_account FOREIGN KEY (account_id) REFERENCES account(account_id)
);

CREATE TABLE bank_transaction (
  transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  account_id INT NOT NULL,
  transaction_type ENUM('DEPOSIT','WITHDRAWAL','TRANSFER_IN','TRANSFER_OUT') NOT NULL,
  amount DECIMAL(14,2) NOT NULL CHECK (amount > 0),
  transaction_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  description VARCHAR(255) NULL,
  reference_number VARCHAR(60) NOT NULL,
  transaction_status ENUM('SUCCESS','PENDING','FAILED') NOT NULL DEFAULT 'SUCCESS',
  INDEX idx_transaction_account_date (account_id, transaction_date),
  INDEX idx_transaction_reference (reference_number),
  CONSTRAINT fk_transaction_account FOREIGN KEY (account_id) REFERENCES account(account_id)
);

CREATE TABLE loan (
  loan_id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  branch_id INT NOT NULL,
  loan_type ENUM('Home Loan','Education Loan','Personal Loan','Vehicle Loan') NOT NULL,
  loan_amount DECIMAL(14,2) NOT NULL CHECK (loan_amount > 0),
  interest_rate DECIMAL(5,2) NOT NULL CHECK (interest_rate >= 0),
  start_date DATE NOT NULL,
  tenure_months INT NOT NULL CHECK (tenure_months > 0),
  loan_status ENUM('Pending','Approved','Rejected','Closed') NOT NULL DEFAULT 'Pending',
  CONSTRAINT fk_loan_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
  CONSTRAINT fk_loan_branch FOREIGN KEY (branch_id) REFERENCES branch(branch_id)
);

CREATE TABLE loan_payment (
  payment_id INT AUTO_INCREMENT PRIMARY KEY,
  loan_id INT NOT NULL,
  payment_date DATE NOT NULL,
  amount DECIMAL(14,2) NOT NULL CHECK (amount > 0),
  payment_mode ENUM('Cash','UPI','Card','Bank Transfer','Cheque') NOT NULL,
  reference_number VARCHAR(60) NOT NULL UNIQUE,
  CONSTRAINT fk_payment_loan FOREIGN KEY (loan_id) REFERENCES loan(loan_id)
);

-- The transaction ledger is the source for balance changes.
DELIMITER //
CREATE TRIGGER trg_transaction_after_insert
AFTER INSERT ON bank_transaction
FOR EACH ROW
BEGIN
  IF NEW.transaction_status = 'SUCCESS' THEN
    IF NEW.transaction_type = 'DEPOSIT' OR NEW.transaction_type = 'TRANSFER_IN' THEN
      UPDATE account SET balance = balance + NEW.amount WHERE account_id = NEW.account_id;
    ELSEIF NEW.transaction_type = 'WITHDRAWAL' OR NEW.transaction_type = 'TRANSFER_OUT' THEN
      UPDATE account SET balance = balance - NEW.amount WHERE account_id = NEW.account_id;
    END IF;
  END IF;
END//
DELIMITER ;

CREATE VIEW vw_account_details AS
SELECT a.account_id, a.account_number, a.account_type, a.opening_date, a.balance, a.status,
       b.branch_name, b.ifsc_code,
       GROUP_CONCAT(CONCAT(c.first_name, ' ', c.last_name) SEPARATOR ', ') AS account_holders
FROM account a
JOIN branch b ON a.branch_id = b.branch_id
LEFT JOIN account_holder ah ON a.account_id = ah.account_id
LEFT JOIN customer c ON ah.customer_id = c.customer_id
GROUP BY a.account_id, a.account_number, a.account_type, a.opening_date, a.balance, a.status,
         b.branch_name, b.ifsc_code;

DELIMITER //
CREATE FUNCTION fn_account_balance(p_account_id INT)
RETURNS DECIMAL(14,2)
READS SQL DATA
BEGIN
  DECLARE current_balance DECIMAL(14,2);
  SELECT balance INTO current_balance FROM account WHERE account_id = p_account_id;
  RETURN COALESCE(current_balance, 0.00);
END//
CREATE PROCEDURE sp_customer_account_summary(IN p_customer_id INT)
BEGIN
  SELECT c.customer_id, CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
         a.account_number, a.account_type, a.balance, a.status
  FROM customer c
  LEFT JOIN account_holder ah ON c.customer_id = ah.customer_id
  LEFT JOIN account a ON ah.account_id = a.account_id
  WHERE c.customer_id = p_customer_id;
END//
DELIMITER ;

-- Demo branch and employees. Sample customers/accounts are intentionally not seeded;
-- create them from the web app so you can demonstrate the full workflow.
INSERT INTO branch (branch_name, ifsc_code, address, city, state, contact_number)
VALUES
('Kashi Main Branch', 'KASH0001001', '12 Demo Road', 'Kashi Nagar', 'Kerala', '04933-220001'),
('Kashi City Branch', 'KASH0001002', '8 Sample Street', 'Kashi Nagar', 'Kerala', '04933-220002');

INSERT INTO employee (employee_name, mobile, email, designation, salary, joining_date, branch_id)
VALUES
('Demo Manager', '9000000001', 'manager@example.test', 'Branch Manager', 45000.00, '2024-01-10', 1),
('Demo Officer', '9000000002', 'officer@example.test', 'Bank Officer', 28000.00, '2024-06-15', 2);
