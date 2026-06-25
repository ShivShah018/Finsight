-- FinSight Migration v4 — soft-delete, split transactions, bills, auto-fund
USE finsight;

ALTER TABLE transactions
    ADD COLUMN deleted_at TIMESTAMP NULL DEFAULT NULL AFTER receipt_path,
    ADD COLUMN is_bill TINYINT(1) DEFAULT 0 AFTER currency,
    ADD COLUMN parent_transaction_id INT DEFAULT NULL AFTER receipt_path,
    ADD COLUMN split_note VARCHAR(255) DEFAULT NULL AFTER parent_transaction_id,
    ADD INDEX idx_deleted (user_id, deleted_at),
    ADD INDEX idx_bills (user_id, is_bill, transaction_date);

ALTER TABLE savings_goals
    ADD COLUMN auto_fund_amount DECIMAL(12,2) DEFAULT 0.00 AFTER current_amount,
    ADD COLUMN auto_fund_category_id INT DEFAULT NULL AFTER auto_fund_amount,
    ADD INDEX idx_auto_fund (user_id, auto_fund_category_id);
