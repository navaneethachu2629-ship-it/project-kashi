import os
from decimal import Decimal, InvalidOperation
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "project-kashi-demo-key")


def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "6235"),
        database=os.getenv("DB_NAME", "project_kashi"),
        port=int(os.getenv("DB_PORT", "3306")),
    )


def fetch_all(sql, params=()):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def fetch_one(sql, params=()):
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def valid_amount(raw):
    try:
        amount = Decimal(raw).quantize(Decimal("0.01"))
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        return amount
    except (InvalidOperation, TypeError):
        raise ValueError("Enter a valid amount, for example 500.00.")


@app.route("/")
def dashboard():
    stats = fetch_one("""
        SELECT
          (SELECT COUNT(*) FROM customer) AS customers,
          (SELECT COUNT(*) FROM account WHERE status = 'Active') AS active_accounts,
          (SELECT COALESCE(SUM(balance), 0) FROM account WHERE status = 'Active') AS total_balance,
          (SELECT COUNT(*) FROM bank_transaction) AS transactions
    """)
    recent = fetch_all("""
        SELECT t.transaction_id, t.transaction_type, t.amount, t.transaction_date,
               t.transaction_status, a.account_number
        FROM bank_transaction t JOIN account a ON a.account_id = t.account_id
        ORDER BY t.transaction_date DESC, t.transaction_id DESC LIMIT 8
    """)
    return render_template("dashboard.html", stats=stats, recent=recent)


@app.route("/customers")
def customers():
    rows = fetch_all("""
        SELECT c.*, COUNT(ah.account_id) AS account_count
        FROM customer c LEFT JOIN account_holder ah ON c.customer_id = ah.customer_id
        GROUP BY c.customer_id ORDER BY c.customer_id DESC
    """)
    return render_template("customers.html", customers=rows)


@app.route("/customers/new", methods=["GET", "POST"])
def new_customer():
    if request.method == "POST":
        data = (
            request.form.get("first_name", "").strip(),
            request.form.get("last_name", "").strip(),
            request.form.get("date_of_birth") or None,
            request.form.get("gender") or None,
            request.form.get("mobile", "").strip(),
            request.form.get("email", "").strip() or None,
            request.form.get("address", "").strip() or None,
            request.form.get("city", "").strip() or None,
        )
        if not data[0] or not data[1] or not data[4]:
            flash("First name, last name and mobile are required.", "error")
            return render_template("customer_form.html")
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO customer
                (first_name, last_name, date_of_birth, gender, mobile, email, address, city)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, data)
            conn.commit()
            flash(f"Customer created successfully (ID: {cur.lastrowid}).", "success")
            return redirect(url_for("customers"))
        except Error as exc:
            conn.rollback()
            flash(f"Could not save customer: {exc}", "error")
        finally:
            cur.close()
            conn.close()
    return render_template("customer_form.html")


@app.route("/accounts")
def accounts():
    rows = fetch_all("""
        SELECT a.account_id, a.account_number, a.account_type, a.opening_date, a.balance, a.status,
               b.branch_name, GROUP_CONCAT(CONCAT(c.first_name, ' ', c.last_name) SEPARATOR ', ') AS holders
        FROM account a
        JOIN branch b ON a.branch_id = b.branch_id
        LEFT JOIN account_holder ah ON a.account_id = ah.account_id
        LEFT JOIN customer c ON ah.customer_id = c.customer_id
        GROUP BY a.account_id ORDER BY a.account_id DESC
    """)
    return render_template("accounts.html", accounts=rows)


@app.route("/accounts/new", methods=["GET", "POST"])
def new_account():
    customer_rows = fetch_all("SELECT customer_id, first_name, last_name, mobile FROM customer ORDER BY first_name")
    branch_rows = fetch_all("SELECT branch_id, branch_name, ifsc_code FROM branch ORDER BY branch_name")
    if request.method == "POST":
        try:
            customer_id = int(request.form.get("customer_id", ""))
            branch_id = int(request.form.get("branch_id", ""))
            account_type = request.form.get("account_type", "")
            opening_amount = valid_amount(request.form.get("opening_amount", "0"))
            if account_type not in ("Saving", "Current", "Salary"):
                raise ValueError("Choose a valid account type.")
            conn = get_db()
            cur = conn.cursor()
            try:
                cur.execute("SELECT customer_id FROM customer WHERE customer_id=%s", (customer_id,))
                if not cur.fetchone():
                    raise ValueError("Selected customer does not exist.")
                cur.execute("SELECT branch_id FROM branch WHERE branch_id=%s", (branch_id,))
                if not cur.fetchone():
                    raise ValueError("Selected branch does not exist.")
                account_number = "KASHI" + str(100000000 + int(date.today().strftime("%y%m%d")) * 100 + customer_id)
                cur.execute("""
                    INSERT INTO account (account_number, account_type, opening_date, balance, status, branch_id)
                    VALUES (%s,%s,CURDATE(),0,'Active',%s)
                """, (account_number, account_type, branch_id))
                account_id = cur.lastrowid
                cur.execute("""
                    INSERT INTO account_holder (customer_id, account_id, holder_since, holder_type)
                    VALUES (%s,%s,CURDATE(),'Primary')
                """, (customer_id, account_id))
                if opening_amount > 0:
                    cur.execute("""
                        INSERT INTO bank_transaction
                        (account_id, transaction_type, amount, description, reference_number, transaction_status)
                        VALUES (%s,'DEPOSIT',%s,'Opening deposit',%s,'SUCCESS')
                    """, (account_id, opening_amount, f"OPEN-{account_id}"))
                conn.commit()
                flash(f"Account opened successfully. Account number: {account_number}", "success")
                return redirect(url_for("accounts"))
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()
                conn.close()
        except (ValueError, Error) as exc:
            flash(str(exc), "error")
    return render_template("account_form.html", customers=customer_rows, branches=branch_rows)


@app.route("/transactions")
def transactions():
    rows = fetch_all("""
        SELECT t.*, a.account_number
        FROM bank_transaction t JOIN account a ON t.account_id=a.account_id
        ORDER BY t.transaction_date DESC, t.transaction_id DESC LIMIT 100
    """)
    return render_template("transactions.html", transactions=rows)


@app.route("/transactions/new", methods=["GET", "POST"])
def new_transaction():
    account_rows = fetch_all("SELECT account_id, account_number, balance FROM account WHERE status='Active' ORDER BY account_number")
    if request.method == "POST":
        action = request.form.get("action", "")
        try:
            account_id = int(request.form.get("account_id", ""))
            amount = valid_amount(request.form.get("amount", ""))
            description = request.form.get("description", "").strip() or None
            conn = get_db()
            cur = conn.cursor(dictionary=True)
            try:
                conn.start_transaction()
                cur.execute("SELECT account_id, balance, status FROM account WHERE account_id=%s FOR UPDATE", (account_id,))
                account = cur.fetchone()
                if not account or account["status"] != "Active":
                    raise ValueError("Account not found or not active.")
                if action == "WITHDRAWAL" and Decimal(str(account["balance"])) < amount:
                    raise ValueError("Insufficient balance.")
                if action not in ("DEPOSIT", "WITHDRAWAL"):
                    raise ValueError("Choose Deposit or Withdrawal.")
                ref = f"TXN-{date.today().strftime('%Y%m%d')}-{os.urandom(3).hex().upper()}"
                cur.execute("""
                    INSERT INTO bank_transaction
                    (account_id, transaction_type, amount, description, reference_number, transaction_status)
                    VALUES (%s,%s,%s,%s,%s,'SUCCESS')
                """, (account_id, action, amount, description, ref))
                conn.commit()
                flash(f"{action.title()} completed successfully. Reference: {ref}", "success")
                return redirect(url_for("transactions"))
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()
                conn.close()
        except (ValueError, Error) as exc:
            flash(str(exc), "error")
    return render_template("transaction_form.html", accounts=account_rows)


@app.route("/transfers", methods=["GET", "POST"])
def transfers():
    account_rows = fetch_all("SELECT account_id, account_number, balance FROM account WHERE status='Active' ORDER BY account_number")
    if request.method == "POST":
        try:
            source_id = int(request.form.get("source_account_id", ""))
            destination_id = int(request.form.get("destination_account_id", ""))
            amount = valid_amount(request.form.get("amount", ""))
            if source_id == destination_id:
                raise ValueError("Source and destination accounts must be different.")
            conn = get_db()
            cur = conn.cursor(dictionary=True)
            try:
                conn.start_transaction()
                ids = sorted([source_id, destination_id])
                cur.execute("SELECT account_id, account_number, balance, status FROM account WHERE account_id IN (%s,%s) ORDER BY account_id FOR UPDATE", tuple(ids))
                locked = {row["account_id"]: row for row in cur.fetchall()}
                source = locked.get(source_id)
                destination = locked.get(destination_id)
                if not source or not destination or source["status"] != "Active" or destination["status"] != "Active":
                    raise ValueError("Both accounts must exist and be active.")
                if Decimal(str(source["balance"])) < amount:
                    raise ValueError("Insufficient balance for transfer.")
                ref = f"TRF-{date.today().strftime('%Y%m%d')}-{os.urandom(3).hex().upper()}"
                cur.execute("""
                    INSERT INTO bank_transaction
                    (account_id, transaction_type, amount, description, reference_number, transaction_status)
                    VALUES (%s,'TRANSFER_OUT',%s,%s,%s,'SUCCESS')
                """, (source_id, amount, f"Transfer to {destination['account_number']}", ref))
                cur.execute("""
                    INSERT INTO bank_transaction
                    (account_id, transaction_type, amount, description, reference_number, transaction_status)
                    VALUES (%s,'TRANSFER_IN',%s,%s,%s,'SUCCESS')
                """, (destination_id, amount, f"Transfer from {source['account_number']}", ref))
                conn.commit()
                flash(f"Transfer completed successfully. Reference: {ref}", "success")
                return redirect(url_for("transactions"))
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()
                conn.close()
        except (ValueError, Error) as exc:
            flash(str(exc), "error")
    return render_template("transfer_form.html", accounts=account_rows)


@app.route("/loans")
def loans():
    rows = fetch_all("""
        SELECT l.*, CONCAT(c.first_name, ' ', c.last_name) AS customer_name, b.branch_name
        FROM loan l JOIN customer c ON l.customer_id=c.customer_id
        JOIN branch b ON l.branch_id=b.branch_id ORDER BY l.loan_id DESC
    """)
    return render_template("loans.html", loans=rows)


@app.route("/loans/new", methods=["GET", "POST"])
def new_loan():
    customer_rows = fetch_all("SELECT customer_id, first_name, last_name FROM customer ORDER BY first_name")
    branch_rows = fetch_all("SELECT branch_id, branch_name FROM branch ORDER BY branch_name")
    if request.method == "POST":
        try:
            customer_id = int(request.form.get("customer_id", ""))
            branch_id = int(request.form.get("branch_id", ""))
            loan_type = request.form.get("loan_type", "")
            amount = valid_amount(request.form.get("loan_amount", ""))
            rate = Decimal(request.form.get("interest_rate", "0"))
            tenure = int(request.form.get("tenure_months", "0"))
            if loan_type not in ("Home Loan", "Education Loan", "Personal Loan", "Vehicle Loan"):
                raise ValueError("Choose a valid loan type.")
            if rate < 0 or tenure < 1:
                raise ValueError("Interest rate cannot be negative and tenure must be at least one month.")
            conn = get_db()
            cur = conn.cursor()
            try:
                cur.execute("""
                    INSERT INTO loan (customer_id, branch_id, loan_type, loan_amount, interest_rate, start_date, tenure_months, loan_status)
                    VALUES (%s,%s,%s,%s,%s,CURDATE(),%s,'Pending')
                """, (customer_id, branch_id, loan_type, amount, rate, tenure))
                conn.commit()
                flash("Loan application saved with Pending status (demo only).", "success")
                return redirect(url_for("loans"))
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()
                conn.close()
        except (ValueError, Error) as exc:
            flash(str(exc), "error")
    return render_template("loan_form.html", customers=customer_rows, branches=branch_rows)


@app.route("/documentation")
def documentation():
    return render_template("documentation.html")


@app.errorhandler(Error)
def database_error(error):
    return render_template("error.html", message="Database connection or query failed. Check MySQL is running and schema.sql has been imported.", detail=str(error)), 500


if __name__ == "__main__":
    app.run(debug=True)
