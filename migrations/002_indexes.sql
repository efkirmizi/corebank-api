-- 002_indexes
-- The original schema had only primary and unique keys, so every foreign-key
-- join and every reporting query did a full table scan. These indexes back the
-- foreign keys and the columns the analytical queries filter and group by.

CREATE INDEX idx_user_customer ON user (customer_id);
CREATE INDEX idx_account_customer ON account (customer_id);
CREATE INDEX idx_account_branch ON account (branch_id);
CREATE INDEX idx_loan_customer ON loan (customer_id);
CREATE INDEX idx_loanpayment_loan ON loan_payment (loan_id);
CREATE INDEX idx_employee_branch ON employee (branch_id);
CREATE INDEX idx_card_account ON card (account_id);
CREATE INDEX idx_transaction_from ON transaction (from_account_id);
CREATE INDEX idx_transaction_to ON transaction (to_account_id);
CREATE INDEX idx_ticket_customer ON customer_support (customer_id);
CREATE INDEX idx_ticket_employee ON customer_support (employee_id);
CREATE INDEX idx_ticket_status ON customer_support (status);
CREATE INDEX idx_creditscore_customer ON credit_score (customer_id);
