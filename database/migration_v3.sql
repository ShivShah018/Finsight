-- =====================================================================
-- FinSight Migration v3 — budget limits, recurring transactions, receipts
-- =====================================================================

USE finsight;

-- 1. Budget limits per category
CREATE TABLE IF NOT EXISTS budget_limits (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT             NOT NULL,
    category_id   INT             NOT NULL,
    monthly_limit DECIMAL(12, 2)  NOT NULL CHECK (monthly_limit > 0),
    created_at    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)     REFERENCES users(id)       ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id)   ON DELETE CASCADE,
    UNIQUE KEY uq_user_category_budget (user_id, category_id)
) ENGINE=InnoDB;

-- 2. Recurring transactions template
CREATE TABLE IF NOT EXISTS recurring_transactions (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT             NOT NULL,
    category_id   INT             NOT NULL,
    amount        DECIMAL(12, 2)  NOT NULL CHECK (amount > 0),
    type          ENUM('income', 'expense') NOT NULL,
    description   VARCHAR(255)    DEFAULT NULL,
    currency      CHAR(3)         DEFAULT 'INR',
    frequency     ENUM('monthly','weekly','yearly') DEFAULT 'monthly',
    next_due_date DATE            NOT NULL,
    is_active     TINYINT(1)      DEFAULT 1,
    created_at    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)     REFERENCES users(id)       ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id)   ON DELETE CASCADE
) ENGINE=InnoDB;

-- 3. Receipt image path on transactions
ALTER TABLE transactions
    ADD COLUMN receipt_path VARCHAR(500) DEFAULT NULL AFTER description;
