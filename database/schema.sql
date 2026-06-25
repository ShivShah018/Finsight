-- =====================================================================
-- FinSight: Budget Planner with Savings Goals
-- Database Schema for MySQL
-- =====================================================================

CREATE DATABASE IF NOT EXISTS finsight
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE finsight;

-- -----------------------------------------------------------
-- 1. USERS
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    full_name     VARCHAR(100)    NOT NULL,
    email         VARCHAR(150)    NOT NULL UNIQUE,
    password_hash VARCHAR(255)    NOT NULL,
    currency      CHAR(3)         DEFAULT 'USD',
    created_at    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- -----------------------------------------------------------
-- 2. CATEGORIES
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT             NOT NULL,
    name          VARCHAR(60)     NOT NULL,
    type          ENUM('income', 'expense') NOT NULL,
    icon          VARCHAR(10)     DEFAULT '📁',
    color         VARCHAR(7)      DEFAULT '#6366f1',
    created_at    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_user_category (user_id, name, type)
) ENGINE=InnoDB;

-- -----------------------------------------------------------
-- 3. TRANSACTIONS
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT             NOT NULL,
    category_id   INT             NOT NULL,
    amount        DECIMAL(12, 2)  NOT NULL CHECK (amount > 0),
    type          ENUM('income', 'expense') NOT NULL,
    description   VARCHAR(255)    DEFAULT NULL,
    transaction_date DATE         NOT NULL,
    created_at    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)     REFERENCES users(id)       ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id)   ON DELETE RESTRICT,

    INDEX idx_user_date (user_id, transaction_date)
) ENGINE=InnoDB;

-- -----------------------------------------------------------
-- 4. SAVINGS_GOALS
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS savings_goals (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT             NOT NULL,
    name            VARCHAR(120)    NOT NULL,
    target_amount   DECIMAL(12, 2)  NOT NULL CHECK (target_amount > 0),
    current_amount  DECIMAL(12, 2)  DEFAULT 0.00,
    deadline        DATE            DEFAULT NULL,
    status          ENUM('active', 'completed', 'cancelled') DEFAULT 'active',
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------------
-- 5. DEFAULT CATEGORIES (seeded after a user is created)
-- -----------------------------------------------------------
-- Run these INSERTS programmatically after registering a user.
-- Example income categories:  Salary, Freelance, Investments, Other Income
-- Example expense categories: Food & Dining, Rent, Transport, Utilities,
--                              Entertainment, Healthcare, Shopping, Education, Other
