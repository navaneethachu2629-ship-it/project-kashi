# Project Kashi — Banking Management System (Demo)

A classroom/demo project for learning database design and the three-layer flow:
**HTML/CSS frontend → Flask/Python backend → MySQL database**.

> This is an educational simulation only. It is not a real banking application and must not be used to store real customer data or move real money.

## Features
- Create customer records and save them in MySQL.
- Open Saving, Current, or Salary accounts linked to customers and branches.
- Opening deposit, deposits, withdrawals, and transfers.
- Transaction ledger and recent activity dashboard.
- Demo loan application page (loan feature is optional in the brief).
- SQL schema includes primary/foreign keys, constraints, a view, a stored function, a stored procedure, and a trigger.
- `queries.sql` contains more than 10 business queries.

## Requirements
- Python 3.10+
- MySQL 8.0+
- A terminal/command prompt

## Setup

### 1. Create and activate a virtual environment
Windows:
```powershell
py -m venv .venv
.venv\Scripts\activate
```
macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Python packages
```bash
pip install -r requirements.txt
```

### 3. Create the database
Start MySQL, then import `schema.sql`.

With MySQL command line:
```bash
mysql -u root -p < schema.sql
```
Enter your MySQL password when prompted. The script creates the `project_kashi` database and demo branches.

Alternatively, open `schema.sql` in MySQL Workbench and execute it.

### 4. Configure database connection
Set environment variables before running, or edit the defaults near the top of `app.py`.

Windows PowerShell example:
```powershell
$env:DB_HOST="localhost"
$env:DB_USER="root"
$env:DB_PASSWORD="your_mysql_password"
$env:DB_NAME="project_kashi"
```

macOS/Linux example:
```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD='your_mysql_password'
export DB_NAME=project_kashi
```

### 5. Run the application
```bash
python app.py
```
Open `http://127.0.0.1:5000` in your browser.

## Demo walkthrough
1. Open **Customers → Add customer** and save a sample customer.
2. Open **Accounts → Open account**, select that customer and a branch, and enter an opening deposit (or `0`).
3. Open **Transactions → New deposit/withdrawal** and make a small demo transaction.
4. Open **Transfer** and move a demo amount between two accounts. For this, create two accounts first.
5. Review transaction history and account balances.
6. Open `queries.sql` in MySQL Workbench and run selected queries.
7. Open **Documentation** to review relationships and cardinalities.

## Database model (summary)
- `customer` 1—M `account_holder`
- `account` 1—M `account_holder`
- `branch` 1—M `account`
- `branch` 1—M `employee`
- `account` 1—M `bank_transaction`
- `customer` 1—M `loan`
- `branch` 1—M `loan`
- `loan` 1—M `loan_payment`

`account_holder` resolves the many-to-many relationship between customers and accounts, allowing joint accounts.

## Important implementation notes
- The SQL trigger updates account balances when a successful ledger transaction is inserted.
- The backend uses MySQL transactions and row locks for withdrawals/transfers to reduce race conditions.
- The demo generates a simple account number. For a production system, account-number generation, authentication, authorization, audit logging, fraud controls, encryption, backups, regulatory requirements, and independent security review would all need substantial work.
- Do not deploy this demo publicly. Flask debug mode is enabled for local development only.

## Troubleshooting
- **Access denied**: check `DB_USER` and `DB_PASSWORD`.
- **Unknown database**: import `schema.sql`.
- **Can't connect to MySQL**: ensure the MySQL service is running and `DB_HOST`/`DB_PORT` are correct.
- **No customer in account form**: create a customer first.
- **Transfer needs two accounts**: open two accounts before demonstrating a transfer.
