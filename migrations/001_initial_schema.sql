-- 001_initial_schema
-- The eleven core tables. Foreign keys are named explicitly.
--
-- Correction vs. the original course-project schema: loan.customer_id and
-- loan_payment.loan_id are NOT NULL, so their foreign keys cannot use
-- ON DELETE SET NULL. MySQL 8 rejects that combination outright (error 1830),
-- so the original init_db() could not run here at all. Both use ON DELETE
-- RESTRICT, which is what a NOT NULL owning column actually means: you cannot
-- delete a customer who still has loans, or a loan that still has payments.

CREATE TABLE IF NOT EXISTS customer (
    customer_id CHAR(36) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    zip_code VARCHAR(20) NOT NULL,
    wage_declaration DECIMAL(15, 2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user (
    user_id CHAR(36) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('ADMIN', 'USER') NOT NULL DEFAULT 'USER',
    customer_id CHAR(36),
    CONSTRAINT fk_user_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS branch (
    branch_id CHAR(36) PRIMARY KEY,
    branch_name VARCHAR(100) UNIQUE NOT NULL,
    address_line1 VARCHAR(100) NOT NULL,
    address_line2 VARCHAR(100),
    city VARCHAR(100) NOT NULL,
    zip_code VARCHAR(20) NOT NULL,
    phone_number VARCHAR(15) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS account (
    account_id CHAR(36) PRIMARY KEY,
    customer_id CHAR(36) NOT NULL,
    account_type ENUM('CHECKING', 'SAVINGS') NOT NULL,
    balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    creation_date DATETIME NOT NULL,
    branch_id CHAR(36) NOT NULL,
    CONSTRAINT fk_account_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_account_branch FOREIGN KEY (branch_id) REFERENCES branch(branch_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT check_balance_positive CHECK (balance >= 0)
);

CREATE TABLE IF NOT EXISTS loan (
    loan_id CHAR(36) PRIMARY KEY,
    customer_id CHAR(36) NOT NULL,
    loan_type ENUM('HOME', 'AUTO', 'PERSONAL') NOT NULL,
    principal_amount DECIMAL(15, 2) NOT NULL,
    interest_rate DECIMAL(5, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status ENUM('ACTIVE', 'PAID_OFF', 'DEFAULT') NOT NULL,
    CONSTRAINT fk_loan_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT check_principal_positive CHECK (principal_amount > 0),
    CONSTRAINT check_interest_non_negative CHECK (interest_rate >= 0),
    CONSTRAINT check_dates_valid CHECK (start_date < end_date)
);

CREATE TABLE IF NOT EXISTS loan_payment (
    loan_payment_id CHAR(36) PRIMARY KEY,
    loan_id CHAR(36) NOT NULL,
    payment_date DATETIME NOT NULL,
    payment_amount DECIMAL(15, 2) NOT NULL,
    remaining_balance DECIMAL(15, 2),
    CONSTRAINT fk_loanpayment_loan FOREIGN KEY (loan_id) REFERENCES loan(loan_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT check_payment_positive CHECK (payment_amount > 0),
    CONSTRAINT check_remaining_non_negative CHECK (remaining_balance >= 0)
);

CREATE TABLE IF NOT EXISTS employee (
    employee_id CHAR(36) PRIMARY KEY,
    branch_id CHAR(36) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    position VARCHAR(100) NOT NULL,
    hire_date DATETIME NOT NULL,
    phone_number VARCHAR(15) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    CONSTRAINT fk_employee_branch FOREIGN KEY (branch_id) REFERENCES branch(branch_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS card (
    card_id CHAR(36) PRIMARY KEY,
    account_id CHAR(36) NOT NULL,
    card_type ENUM('DEBIT', 'CREDIT') NOT NULL,
    card_number VARCHAR(16) UNIQUE NOT NULL,
    expiration_date DATE NOT NULL,
    cvv VARCHAR(3) NOT NULL,
    status ENUM('ACTIVE', 'BLOCKED', 'EXPIRED') NOT NULL,
    CONSTRAINT fk_card_account FOREIGN KEY (account_id) REFERENCES account(account_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS transaction (
    transaction_id CHAR(36) PRIMARY KEY,
    from_account_id CHAR(36) NOT NULL,
    to_account_id CHAR(36),
    transaction_type ENUM('DEPOSIT', 'WITHDRAWAL', 'TRANSFER') NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    transaction_timestamp DATETIME NOT NULL,
    CONSTRAINT fk_transaction_from FOREIGN KEY (from_account_id) REFERENCES account(account_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_transaction_to FOREIGN KEY (to_account_id) REFERENCES account(account_id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT check_amount_positive CHECK (amount > 0)
);

CREATE TABLE IF NOT EXISTS customer_support (
    ticket_id CHAR(36) PRIMARY KEY,
    customer_id CHAR(36) NOT NULL,
    employee_id CHAR(36) NOT NULL,
    issue_description TEXT NOT NULL,
    status ENUM('OPEN', 'IN_PROGRESS', 'RESOLVED') NOT NULL,
    created_date DATETIME NOT NULL,
    resolved_date DATETIME,
    CONSTRAINT fk_ticket_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_ticket_employee FOREIGN KEY (employee_id) REFERENCES employee(employee_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS credit_score (
    credit_score_id CHAR(36) PRIMARY KEY,
    customer_id CHAR(36) NOT NULL,
    score DECIMAL(5, 2) NOT NULL,
    risk_category VARCHAR(50) NOT NULL,
    computed_by_system BOOLEAN,
    CONSTRAINT fk_creditscore_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);
