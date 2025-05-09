from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flash messages

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'pranavsk',
    'database': 'cash_tally'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('SELECT * FROM daily_transactions')
        transactions = cursor.fetchall()

        cursor.execute('SELECT * FROM store_expenses')
        expenses = cursor.fetchall()

        cursor.execute('SELECT * FROM bank_deposits')
        deposits = cursor.fetchall()

        cursor.execute('SELECT * FROM cash_flow')
        cashflows = cursor.fetchall()

        return render_template('index.html', 
                            transactions=transactions, 
                            expenses=expenses, 
                            deposits=deposits, 
                            cashflows=cashflows)
    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        return render_template('index.html', 
                            transactions=[], 
                            expenses=[], 
                            deposits=[], 
                            cashflows=[])
    finally:
        cursor.close()
        conn.close()

@app.route('/charts')
def charts():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get sales data for line chart
        cursor.execute("SELECT transaction_date, total_sales FROM daily_transactions ORDER BY transaction_date")
        sales_data = cursor.fetchall()
        sales_labels = [row[0].strftime('%Y-%m-%d') for row in sales_data]
        sales_values = [float(row[1]) for row in sales_data]

        # Get expenses data for bar chart
        cursor.execute("SELECT expense_date, expenses FROM store_expenses ORDER BY expense_date")
        expenses_data = cursor.fetchall()

        # Get deposits data for pie chart
        cursor.execute("SELECT deposit_date, deposit_amount FROM bank_deposits ORDER BY deposit_date")
        deposits_data = cursor.fetchall()

        # Prepare all chart data
        charts_data = {
            'sales': {
                'labels': sales_labels,
                'data': sales_values
            },
            'expenses': {
                'labels': [str(row[0]) for row in expenses_data],
                'data': [float(row[1]) for row in expenses_data]
            },
            'deposits': {
                'labels': [str(row[0]) for row in deposits_data],
                'data': [float(row[1]) for row in deposits_data]
            }
        }

        return render_template('charts.html', charts=json.dumps(charts_data))
    
    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        return render_template('charts.html', charts=json.dumps({
            'sales': {'labels': [], 'data': []},
            'expenses': {'labels': [], 'data': []},
            'deposits': {'labels': [], 'data': []}
        }))
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route("/dashboard")
def dashboard():
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT * FROM daily_transactions")
        transactions = cur.fetchall()

        cur.execute("SELECT * FROM store_expenses")
        expenses = cur.fetchall()

        cur.execute("SELECT * FROM bank_deposits")
        deposits = cur.fetchall()

        return render_template("dashboard.html", 
                            transactions=transactions, 
                            expenses=expenses, 
                            deposits=deposits)
    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        return render_template("dashboard.html", 
                            transactions=[], 
                            expenses=[], 
                            deposits=[])
    finally:
        cur.close()
        conn.close()

@app.route("/add_transaction", methods=["GET", "POST"])
def add_transaction():
    if request.method == "POST":
        try:
            transaction_date = request.form["transaction_date"]
            online_sales = float(request.form["online_sales"])
            credit_card = float(request.form["credit_card"])
            cheque = float(request.form["cheque"])
            gpay = float(request.form["gpay"])

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO daily_transactions 
                (transaction_date, online_sales, credit_card, cheque, gpay)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (transaction_date, online_sales, credit_card, cheque, gpay)
            )
            conn.commit()
            flash("Transaction added successfully!")
            return redirect(url_for("dashboard"))
        except ValueError:
            flash("Invalid number format in transaction data")
            return redirect(url_for("add_transaction"))
        except mysql.connector.Error as err:
            flash(f"Database error: {err}")
            return redirect(url_for("add_transaction"))
        finally:
            if 'conn' in locals():
                conn.close()
    
    # GET request - show form
    return render_template("add_transaction.html")

@app.route("/add_expense", methods=["GET", "POST"])
def add_expense():
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        if request.method == "POST":
            main_id = request.form["main_id"]
            expense_date = request.form["expense_date"]
            expenses = float(request.form["expenses"])

            cur.execute(
                """
                INSERT INTO store_expenses 
                (main_id, expense_date, expenses)
                VALUES (%s, %s, %s)
                """,
                (main_id, expense_date, expenses)
            )
            conn.commit()
            flash("Expense added successfully!")
            return redirect(url_for("dashboard"))

        # GET request - show form with main_ids
        cur.execute("SELECT DISTINCT main_id FROM daily_transactions")
        main_ids = [row['main_id'] for row in cur.fetchall()]
        return render_template("add_expense.html", main_ids=main_ids)

    except ValueError:
        flash("Invalid number format in expense data")
        return redirect(url_for("add_expense"))
    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        return redirect(url_for("add_expense"))
    finally:
        if 'conn' in locals():
            conn.close()

@app.route("/add_deposit", methods=["GET", "POST"])
def add_deposit():
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        if request.method == "POST":
            main_id = request.form["main_id"]
            deposit_date = request.form["deposit_date"]
            deposit_amount = float(request.form["deposit_amount"])

            cur.execute(
                """
                INSERT INTO bank_deposits 
                (main_id, deposit_date, deposit_amount)
                VALUES (%s, %s, %s)
                """,
                (main_id, deposit_date, deposit_amount)
            )
            conn.commit()
            flash("Deposit added successfully!")
            return redirect(url_for("dashboard"))

        # GET request - show form with main_ids
        cur.execute("SELECT DISTINCT main_id FROM daily_transactions")
        main_ids = [row['main_id'] for row in cur.fetchall()]
        return render_template("add_deposit.html", main_ids=main_ids)

    except ValueError:
        flash("Invalid number format in deposit data")
        return redirect(url_for("add_deposit"))
    except mysql.connector.Error as err:
        flash(f"Database error: {err}")
        return redirect(url_for("add_deposit"))
    finally:
        if 'conn' in locals():
            conn.close()


@app.route('/update_transaction', methods=['GET', 'POST'])
def update_transaction():
    conn = get_db_connection()
    cursor = conn.cursor()
    record = None
    if request.method == 'POST':
        if 'search' in request.form:
            search_date = request.form['transaction_date']
            cursor.execute("SELECT * FROM daily_transactions WHERE transaction_date = %s", (search_date,))
            record = cursor.fetchone()
            if not record:
                flash('No transaction found for the given date.', 'warning')
        elif 'update' in request.form:
            online_sales = request.form['online_sales']
            credit_card = request.form['credit_card']
            cheque = request.form['cheque']
            gpay = request.form['gpay']
            transaction_date = request.form['transaction_date']
            cursor.execute("""
                UPDATE daily_transactions SET
                    online_sales=%s, credit_card=%s, cheque=%s, gpay=%s
                WHERE transaction_date=%s
            """, (online_sales, credit_card, cheque, gpay, transaction_date))
            conn.commit()
            flash('Transaction updated successfully!', 'success')
    return render_template('update_transaction.html', record=record)

@app.route('/update_expense', methods=['GET', 'POST'])
def update_expense():
    conn = get_db_connection()
    cursor = conn.cursor()
    record = None
    if request.method == 'POST':
        if 'search' in request.form:
            search_date = request.form['expense_date']
            cursor.execute("SELECT * FROM store_expenses WHERE expense_date = %s", (search_date,))
            record = cursor.fetchone()
            if not record:
                flash('No expense found for the given date.', 'warning')
        elif 'update' in request.form:
            expense_date = request.form['expense_date']
            expenses = request.form['expenses']
            cursor.execute("""
                UPDATE store_expenses SET expenses=%s
                WHERE expense_date=%s
            """, (expenses, expense_date))
            conn.commit()
            flash('Expense updated successfully!', 'success')
    return render_template('update_expense.html', record=record)


@app.route('/update_deposit', methods=['GET', 'POST'])
def update_deposit():
    conn = get_db_connection()
    cursor = conn.cursor()
    record = None
    if request.method == 'POST':
        if 'search' in request.form:            
            search_date = request.form['deposit_date']
            cursor.execute("SELECT * FROM bank_deposits WHERE deposit_date = %s", (search_date,))
            record = cursor.fetchone()
            if not record:
                flash('No deposit found for the given date.', 'warning')
        elif 'update' in request.form:
            deposit_date = request.form['deposit_date']
            deposit_amount = request.form['deposit_amount']
            cursor.execute("""
                UPDATE bank_deposits SET deposit_amount=%s
                WHERE deposit_date=%s
            """, (deposit_amount, deposit_date))
            conn.commit()
            flash('Deposit updated successfully!', 'success')
    return render_template('update_deposit.html', record=record)


if __name__ == '__main__':
    app.run(debug=True)