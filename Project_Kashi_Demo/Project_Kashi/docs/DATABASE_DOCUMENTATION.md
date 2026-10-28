# Project Kashi — Database Documentation

## 1. Purpose
The project is a database-driven banking workflow demonstration. It is intended to explain how HTML forms send data to Flask and how Flask validates and persists that data in MySQL.

## 2. Entities and definitions

| Table | Definition | Primary key |
|---|---|---|
| `customer` | Stores customer profile and contact information. | `customer_id` |
| `branch` | Stores branch name, IFSC-like demo code, location and contact. | `branch_id` |
| `employee` | Stores employee information and the branch where they work. | `employee_id` |
| `account` | Stores account number, type, opening date, balance, status and branch. | `account_id` |
| `account_holder` | Junction table linking customers and accounts; supports joint accounts. | Composite: `customer_id`, `account_id` |
| `bank_transaction` | Ledger of deposits, withdrawals and transfer entries. | `transaction_id` |
| `loan` | Stores a customer's loan application/details. | `loan_id` |
| `loan_payment` | Stores payments made against a loan. | `payment_id` |

## 3. Relationships and cardinality

| Relationship | Cardinality | Explanation |
|---|---|---|
| Branch — Account | 1:M | One branch can manage many accounts; each account belongs to one branch. |
| Branch — Employee | 1:M | One branch can have many employees; each employee belongs to one branch. |
| Customer — Account | M:N through `account_holder` | A customer may hold multiple accounts and an account may have multiple joint holders. |
| Account — Bank transaction | 1:M | An account can have many ledger entries; each entry belongs to one account. |
| Customer — Loan | 1:M | A customer can have multiple loans; each loan is linked to one customer. |
| Branch — Loan | 1:M | A branch can be associated with many loans; each loan references one branch. |
| Loan — Loan payment | 1:M | One loan can have many payment records; each payment references one loan. |

## 4. Integrity rules
- Primary keys uniquely identify each row.
- Foreign keys prevent orphan rows.
- Mobile number and email are unique where provided by the schema.
- Account number and branch IFSC-like code are unique.
- Amounts must be positive; salary and balance cannot be negative under the defined checks.
- Account and transaction types use enumerated values.
- Transfer writes a debit-side `TRANSFER_OUT` row and a credit-side `TRANSFER_IN` row with the same reference.
- Application operations use database transactions to commit all related writes together or roll them back on error.

## 5. Normalization overview
- **1NF:** fields hold atomic values; repeating account holders are stored as separate rows in `account_holder`.
- **2NF:** `account_holder` has a composite key and its holder attributes describe the complete customer-account pairing.
- **3NF:** customer, branch, employee, account, transaction and loan data are separated into their own tables; branch details are not repeated in every account.

This is a teaching-level explanation. A formal normalization proof should inspect every functional dependency in the final schema.

## 6. Trigger, view, function and procedure
- `trg_transaction_after_insert`: adjusts account balance after a successful transaction ledger entry.
- `vw_account_details`: joins accounts, branches and holders into a readable view.
- `fn_account_balance(account_id)`: returns the current balance for an account ID.
- `sp_customer_account_summary(customer_id)`: returns the customer's accounts and balances.

## 7. Three-layer workflow
1. **Frontend:** HTML forms collect customer/account/transaction details.
2. **Backend:** Flask receives the form, validates fields, applies business rules and opens a database transaction.
3. **Database:** MySQL enforces constraints, stores ledger rows and runs the balance trigger.
4. **Response:** Flask redirects to the relevant page and shows a success/error message.

## 8. Demonstration checklist
- Add a customer and verify it in `customer`.
- Open an account and verify `account` and `account_holder`.
- Make a deposit and verify the ledger row and changed balance.
- Attempt a withdrawal larger than the balance; it should be rejected.
- Transfer between two accounts and verify the paired ledger rows share a reference.
- Run at least 10 queries from `queries.sql`.
- Explain one primary key, one foreign key, a many-to-many relationship, a trigger, and a transaction.

## 9. Limitations
This is a local educational demo. It has no login, role-based authorization, KYC, OTP, real payment rail, production-grade audit system or deployment hardening. Never use real personal or financial data.
