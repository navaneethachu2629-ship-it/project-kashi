# Project Kashi — Viva Questions and Short Answers

1. **What is the purpose of this project?**  
   To demonstrate how a database-backed web app works using HTML/CSS, Flask/Python and MySQL.

2. **What are the three layers?**  
   Frontend (HTML/CSS), backend (Flask/Python), and database (MySQL).

3. **What is a primary key?**  
   A column or group of columns that uniquely identifies each row.

4. **What is a foreign key?**  
   A constraint that links a row to a valid row in another table.

5. **Why is `account_holder` needed?**  
   It resolves the many-to-many customer-account relationship and can represent joint account holders.

6. **What is cardinality?**  
   It describes how many records in one entity can relate to records in another entity, such as one branch to many accounts.

7. **Why use a transaction for a transfer?**  
   Both transfer ledger rows must be committed together; if an operation fails, both can be rolled back.

8. **What does the trigger do?**  
   It adjusts the account balance after a successful ledger entry is inserted.

9. **What is a view?**  
   A named query that presents joined data as a virtual table. Here, `vw_account_details` combines account, branch and holder information.

10. **What is a stored procedure?**  
    A stored SQL program that can accept parameters and return query results. Here, `sp_customer_account_summary` accepts a customer ID.

11. **What is a stored function?**  
    A stored SQL routine that returns a value. Here, `fn_account_balance` returns an account balance.

12. **What is normalization?**  
    Organizing data into related tables to reduce duplication and update anomalies.

13. **How does a customer get saved?**  
    The HTML form sends a POST request to Flask; Flask validates values and executes an INSERT query through the MySQL connector.

14. **How is insufficient balance prevented?**  
    Flask locks the account row and checks the balance before inserting a withdrawal/transfer-out entry.

15. **What are the limitations?**  
    This demo has no authentication, production-grade authorization, KYC, real payment integration or deployment hardening.
