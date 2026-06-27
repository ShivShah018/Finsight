-- FinSight Migration v5 — Schema improvements: indexes, foreign keys, constraints
USE finsight;

-- Add indexes for better query performance
ALTER TABLE transactions
    ADD INDEX idx_type_amount (user_id, type, amount),
    ADD INDEX idx_date_type (user_id, transaction_date, type),
    ADD INDEX idx_category_lookup (category_id, user_id);

ALTER TABLE savings_goals
    ADD INDEX idx_status (user_id, status);

ALTER TABLE budget_limits
    ADD INDEX idx_budget_user_category (user_id, category_id);

-- Add CHECK constraints for validation
ALTER TABLE transactions
    ADD CONSTRAINT chk_positive_amount CHECK (amount > 0);

ALTER TABLE savings_goals
    ADD CONSTRAINT chk_positive_target CHECK (target_amount > 0),
    ADD CONSTRAINT chk_current_not_negative CHECK (current_amount >= 0);

ALTER TABLE budget_limits
    ADD CONSTRAINT chk_positive_limit CHECK (monthly_limit > 0);

-- Add ON DELETE CASCADE for budget_limits user reference (if missing)
-- (already has CASCADE from migration_v3)

-- Add preferred_currency default if missing
ALTER TABLE users
    MODIFY preferred_currency CHAR(3) DEFAULT 'INR';
