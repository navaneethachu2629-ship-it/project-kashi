USE project_kashi;

-- 1. List all customers
SELECT * FROM customer ORDER BY customer_id;

-- 2. Show each account with branch and customer/holder names
SELECT * FROM vw_account_details ORDER BY account_id;

-- 3. Total active-account balance by branch
SELECT b.branch_name, SUM(a.balance) AS total_balance
FROM branch b JOIN account a ON a.branch_id=b.branch_id
WHERE a.status='Active'
GROUP BY b.branch_id, b.branch_name;

-- 4. Customers with more than one account
SELECT c.customer_id, c.first_name, c.last_name, COUNT(*) AS account_count
FROM customer c JOIN account_holder ah ON c.customer_id=ah.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name
HAVING COUNT(*) > 1;

-- 5. Transaction history for one account (replace 1 with an account_id)
SELECT t.* FROM bank_transaction t
WHERE t.account_id=1 ORDER BY t.transaction_date DESC;

-- 6. Deposit and withdrawal totals by account
SELECT a.account_number,
       SUM(CASE WHEN t.transaction_type IN ('DEPOSIT','TRANSFER_IN') THEN t.amount ELSE 0 END) AS credits,
       SUM(CASE WHEN t.transaction_type IN ('WITHDRAWAL','TRANSFER_OUT') THEN t.amount ELSE 0 END) AS debits
FROM account a LEFT JOIN bank_transaction t ON a.account_id=t.account_id
GROUP BY a.account_id, a.account_number;

-- 7. Customers who have never opened an account
SELECT c.* FROM customer c
LEFT JOIN account_holder ah ON c.customer_id=ah.customer_id
WHERE ah.account_id IS NULL;

-- 8. Number of transactions per type
SELECT transaction_type, COUNT(*) AS transaction_count, SUM(amount) AS total_amount
FROM bank_transaction GROUP BY transaction_type;

-- 9. Pending loan applications
SELECT l.loan_id, CONCAT(c.first_name,' ',c.last_name) AS customer_name,
       l.loan_type, l.loan_amount, l.loan_status
FROM loan l JOIN customer c ON l.customer_id=c.customer_id
WHERE l.loan_status='Pending';

-- 10. Loan payment totals
SELECT l.loan_id, l.loan_amount, COALESCE(SUM(lp.amount),0) AS total_paid
FROM loan l LEFT JOIN loan_payment lp ON l.loan_id=lp.loan_id
GROUP BY l.loan_id, l.loan_amount;

-- 11. Accounts with balances above 10,000
SELECT account_number, balance FROM account WHERE balance > 10000 ORDER BY balance DESC;

-- 12. Use the stored function
SELECT fn_account_balance(1) AS balance_for_account_1;

-- 13. Use the stored procedure
CALL sp_customer_account_summary(1);

-- 14. Employees by branch
SELECT b.branch_name, e.employee_name, e.designation
FROM employee e JOIN branch b ON e.branch_id=b.branch_id
ORDER BY b.branch_name, e.employee_name;
