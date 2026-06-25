-- Migration v2: Add currency column to transactions
USE finsight;

ALTER TABLE transactions ADD COLUMN currency CHAR(3) DEFAULT 'INR' AFTER type;

-- Add preferred_currency to users
ALTER TABLE users ADD COLUMN preferred_currency CHAR(3) DEFAULT 'INR' AFTER currency;
