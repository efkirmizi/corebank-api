-- demo_data
-- A small but coherent dataset: every endpoint returns something meaningful and
-- the three analytical queries produce interesting rows with their default
-- thresholds. Idempotent (INSERT IGNORE) so repeated container starts are safe.
--
-- Demo logins (username / password):
--   admin / admin123   (ADMIN)
--   alice / alice123   (USER, customer Alice Walker)
--   bob   / bob123     (USER, customer Bob Stone)

-- Branches
INSERT IGNORE INTO branch (branch_id, branch_name, address_line1, address_line2, city, zip_code, phone_number) VALUES
('11111111-1111-1111-1111-111111111111', 'Downtown Branch', '1 Market St', NULL, 'Metropolis', '10001', '2125550100'),
('22222222-2222-2222-2222-222222222222', 'Uptown Branch', '500 High Ave', 'Suite 2', 'Metropolis', '10025', '2125550200');

-- Customers
INSERT IGNORE INTO customer (customer_id, first_name, last_name, date_of_birth, phone_number, email, address_line1, address_line2, city, zip_code, wage_declaration) VALUES
('a0000000-0000-0000-0000-0000000000c1', 'Alice', 'Walker', '1990-04-12', '2125551001', 'alice.walker@example.com', '12 Oak St', NULL, 'Metropolis', '10001', 82000.00),
('a0000000-0000-0000-0000-0000000000c2', 'Bob', 'Stone', '1985-09-30', '2125551002', 'bob.stone@example.com', '34 Pine St', 'Apt 4', 'Metropolis', '10002', 61000.00),
('a0000000-0000-0000-0000-0000000000c3', 'Carol', 'Reed', '1978-01-05', '2125551003', 'carol.reed@example.com', '56 Elm St', NULL, 'Metropolis', '10025', 240000.00);

-- Users (passwords are pbkdf2:sha256 hashes)
INSERT IGNORE INTO user (user_id, username, password, role, customer_id) VALUES
('f0000000-0000-0000-0000-0000000000u1', 'admin', 'pbkdf2:sha256:1000000$tqJGZGrQlDU4dOxm$2c65fd80658f246c22b03fc84cd2a066959c9650810c6cb4c3929b8b8f316850', 'ADMIN', NULL),
('f0000000-0000-0000-0000-0000000000u2', 'alice', 'pbkdf2:sha256:1000000$m2H3FRCNITT2rPxe$40520447a5492a117bba9aa4cf1c3a3dd8c7676102a51491d8cd24e1b299976f', 'USER', 'a0000000-0000-0000-0000-0000000000c1'),
('f0000000-0000-0000-0000-0000000000u3', 'bob', 'pbkdf2:sha256:1000000$S2SGYk1kKz27VLPr$d412624bb9b9dbea53d7ba9c8c7b4655688c8842ebc4685f3f9a9eb1f029103a', 'USER', 'a0000000-0000-0000-0000-0000000000c2');

-- Accounts (Downtown holds three so the branch-conditions report returns it)
INSERT IGNORE INTO account (account_id, customer_id, account_type, balance, creation_date, branch_id) VALUES
('acc00000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-0000000000c1', 'CHECKING', 5000.00, '2024-01-15 09:00:00', '11111111-1111-1111-1111-111111111111'),
('acc00000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-0000000000c1', 'SAVINGS', 15000.00, '2024-01-15 09:05:00', '11111111-1111-1111-1111-111111111111'),
('acc00000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-0000000000c2', 'CHECKING', 3000.00, '2024-02-20 10:00:00', '11111111-1111-1111-1111-111111111111'),
('acc00000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-0000000000c3', 'SAVINGS', 250000.00, '2024-03-01 11:00:00', '22222222-2222-2222-2222-222222222222');

-- Employees (six at Downtown so the branch-conditions report clears its default threshold)
INSERT IGNORE INTO employee (employee_id, branch_id, first_name, last_name, position, hire_date, phone_number, email) VALUES
('e0000000-0000-0000-0000-0000000000e1', '11111111-1111-1111-1111-111111111111', 'Dana', 'Fox', 'Support Agent', '2022-05-01 09:00:00', '2125552001', 'dana.fox@corebank.example'),
('e0000000-0000-0000-0000-0000000000e2', '11111111-1111-1111-1111-111111111111', 'Evan', 'Cole', 'Support Agent', '2022-06-01 09:00:00', '2125552002', 'evan.cole@corebank.example'),
('e0000000-0000-0000-0000-0000000000e3', '11111111-1111-1111-1111-111111111111', 'Faye', 'Kim', 'Teller', '2022-07-01 09:00:00', '2125552003', 'faye.kim@corebank.example'),
('e0000000-0000-0000-0000-0000000000e4', '11111111-1111-1111-1111-111111111111', 'Gary', 'Lee', 'Teller', '2022-08-01 09:00:00', '2125552004', 'gary.lee@corebank.example'),
('e0000000-0000-0000-0000-0000000000e5', '11111111-1111-1111-1111-111111111111', 'Hana', 'Ito', 'Manager', '2021-03-01 09:00:00', '2125552005', 'hana.ito@corebank.example'),
('e0000000-0000-0000-0000-0000000000e6', '11111111-1111-1111-1111-111111111111', 'Ivan', 'Roe', 'Teller', '2023-01-10 09:00:00', '2125552006', 'ivan.roe@corebank.example'),
('e0000000-0000-0000-0000-0000000000e7', '22222222-2222-2222-2222-222222222222', 'Jane', 'Ash', 'Manager', '2021-09-01 09:00:00', '2125552007', 'jane.ash@corebank.example');

-- Cards
INSERT IGNORE INTO card (card_id, account_id, card_type, card_number, expiration_date, cvv, status) VALUES
('ca000000-0000-0000-0000-0000000000d1', 'acc00000-0000-0000-0000-000000000001', 'DEBIT', '4000123412341234', '2028-04-30', '123', 'ACTIVE'),
('ca000000-0000-0000-0000-0000000000d2', 'acc00000-0000-0000-0000-000000000003', 'CREDIT', '5100987698769876', '2027-11-30', '456', 'ACTIVE');

-- Loans
INSERT IGNORE INTO loan (loan_id, customer_id, loan_type, principal_amount, interest_rate, start_date, end_date, status) VALUES
('10a00000-0000-0000-0000-0000000000l1', 'a0000000-0000-0000-0000-0000000000c1', 'HOME', 200000.00, 4.25, '2023-06-01', '2043-06-01', 'ACTIVE'),
('10a00000-0000-0000-0000-0000000000l2', 'a0000000-0000-0000-0000-0000000000c2', 'AUTO', 30000.00, 6.90, '2024-01-01', '2029-01-01', 'ACTIVE');

-- Loan payments
INSERT IGNORE INTO loan_payment (loan_payment_id, loan_id, payment_date, payment_amount, remaining_balance) VALUES
('90a00000-0000-0000-0000-0000000000p1', '10a00000-0000-0000-0000-0000000000l1', '2023-07-01 09:00:00', 1200.00, 198800.00),
('90a00000-0000-0000-0000-0000000000p2', '10a00000-0000-0000-0000-0000000000l2', '2024-02-01 09:00:00', 550.00, 29450.00);

-- Transactions (Carol's savings totals well over the reporting threshold)
INSERT IGNORE INTO transaction (transaction_id, from_account_id, to_account_id, transaction_type, amount, transaction_timestamp) VALUES
('70a00000-0000-0000-0000-0000000000t1', 'acc00000-0000-0000-0000-000000000001', 'acc00000-0000-0000-0000-000000000003', 'TRANSFER', 200.75, '2024-04-01 12:00:00'),
('70a00000-0000-0000-0000-0000000000t2', 'acc00000-0000-0000-0000-000000000004', NULL, 'DEPOSIT', 60000.00, '2024-04-02 12:00:00'),
('70a00000-0000-0000-0000-0000000000t3', 'acc00000-0000-0000-0000-000000000004', NULL, 'DEPOSIT', 30000.00, '2024-04-03 12:00:00');

-- Credit scores
INSERT IGNORE INTO credit_score (credit_score_id, customer_id, score, risk_category, computed_by_system) VALUES
('c5000000-0000-0000-0000-0000000000s1', 'a0000000-0000-0000-0000-0000000000c1', 720.00, 'LOW', TRUE),
('c5000000-0000-0000-0000-0000000000s2', 'a0000000-0000-0000-0000-0000000000c2', 640.00, 'MEDIUM', TRUE),
('c5000000-0000-0000-0000-0000000000s3', 'a0000000-0000-0000-0000-0000000000c3', 800.00, 'LOW', TRUE);

-- Support tickets (Dana Fox resolves two, making her the top resolver)
INSERT IGNORE INTO customer_support (ticket_id, customer_id, employee_id, issue_description, status, created_date, resolved_date) VALUES
('71c00000-0000-0000-0000-0000000000k1', 'a0000000-0000-0000-0000-0000000000c1', 'e0000000-0000-0000-0000-0000000000e1', 'Card declined at merchant', 'RESOLVED', '2024-05-01 09:00:00', '2024-05-01 15:00:00'),
('71c00000-0000-0000-0000-0000000000k2', 'a0000000-0000-0000-0000-0000000000c1', 'e0000000-0000-0000-0000-0000000000e1', 'Dispute on transfer', 'RESOLVED', '2024-05-10 09:00:00', '2024-05-11 10:00:00'),
('71c00000-0000-0000-0000-0000000000k3', 'a0000000-0000-0000-0000-0000000000c2', 'e0000000-0000-0000-0000-0000000000e2', 'Statement request', 'RESOLVED', '2024-05-12 09:00:00', '2024-05-12 12:00:00'),
('71c00000-0000-0000-0000-0000000000k4', 'a0000000-0000-0000-0000-0000000000c2', 'e0000000-0000-0000-0000-0000000000e2', 'Address change', 'OPEN', '2024-06-01 09:00:00', NULL);
