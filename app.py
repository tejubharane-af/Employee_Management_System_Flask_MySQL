from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
import os

app = Flask(__name__)
app.secret_key = "employee-management-demo-key"

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "Tejaswini@12"),
    "database": os.getenv("DB_NAME", "employee_management")
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

@app.route("/")
def dashboard():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS total FROM employees")
    total = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) AS total FROM departments")
    departments = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) AS total FROM employee_records")
    records = cur.fetchone()["total"]
    cur.execute("""
        SELECT e.id, e.name, e.email, e.position, d.name AS department
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.id
        ORDER BY e.id DESC LIMIT 5
    """)
    recent = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("dashboard.html", total=total, departments=departments,
                           records=records, recent=recent)

@app.route("/employees")
def employees():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT e.*, d.name AS department
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.id
        ORDER BY e.id DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("employees.html", employees=rows)

@app.route("/employees/add", methods=["GET", "POST"])
def add_employee():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM departments ORDER BY name")
    departments = cur.fetchall()

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        position = request.form["position"].strip()
        department_id = request.form["department_id"]
        joining_date = request.form["joining_date"]

        cur.execute("""
            INSERT INTO employees
            (name, email, phone, position, department_id, joining_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, email, phone, position, department_id, joining_date))
        conn.commit()
        cur.close()
        conn.close()
        flash("Employee added successfully.", "success")
        return redirect(url_for("employees"))

    cur.close()
    conn.close()
    return render_template("employee_form.html", departments=departments,
                           employee=None, title="Add Employee")

@app.route("/employees/edit/<int:id>", methods=["GET", "POST"])
def edit_employee(id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM departments ORDER BY name")
    departments = cur.fetchall()

    if request.method == "POST":
        cur.execute("""
            UPDATE employees SET name=%s, email=%s, phone=%s, position=%s,
            department_id=%s, joining_date=%s WHERE id=%s
        """, (
            request.form["name"].strip(),
            request.form["email"].strip(),
            request.form["phone"].strip(),
            request.form["position"].strip(),
            request.form["department_id"],
            request.form["joining_date"],
            id
        ))
        conn.commit()
        cur.close()
        conn.close()
        flash("Employee updated successfully.", "success")
        return redirect(url_for("employees"))

    cur.execute("SELECT * FROM employees WHERE id=%s", (id,))
    employee = cur.fetchone()
    cur.close()
    conn.close()
    return render_template("employee_form.html", departments=departments,
                           employee=employee, title="Edit Employee")

@app.route("/employees/delete/<int:id>", methods=["POST"])
def delete_employee(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM employees WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Employee deleted successfully.", "success")
    return redirect(url_for("employees"))

@app.route("/departments", methods=["GET", "POST"])
def departments():
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form["name"].strip()
        if name:
            cur.execute("INSERT INTO departments (name) VALUES (%s)", (name,))
            conn.commit()
            flash("Department added successfully.", "success")
        return redirect(url_for("departments"))

    cur.execute("""
        SELECT d.id, d.name, COUNT(e.id) AS employee_count
        FROM departments d
        LEFT JOIN employees e ON d.id = e.department_id
        GROUP BY d.id, d.name
        ORDER BY d.name
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("departments.html", departments=rows)

@app.route("/departments/delete/<int:id>", methods=["POST"])
def delete_department(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM employees WHERE department_id=%s", (id,))
    count = cur.fetchone()[0]
    if count:
        flash("Cannot delete a department that has employees.", "error")
    else:
        cur.execute("DELETE FROM departments WHERE id=%s", (id,))
        conn.commit()
        flash("Department deleted successfully.", "success")
    cur.close()
    conn.close()
    return redirect(url_for("departments"))

@app.route("/records")
def records():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT r.*, e.name AS employee_name
        FROM employee_records r
        JOIN employees e ON r.employee_id = e.id
        ORDER BY r.record_date DESC, r.id DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("records.html", records=rows)

@app.route("/records/add", methods=["GET", "POST"])
def add_record():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, name FROM employees ORDER BY name")
    employees = cur.fetchall()

    if request.method == "POST":
        cur.execute("""
            INSERT INTO employee_records
            (employee_id, record_type, description, record_date)
            VALUES (%s, %s, %s, %s)
        """, (
            request.form["employee_id"],
            request.form["record_type"],
            request.form["description"].strip(),
            request.form["record_date"]
        ))
        conn.commit()
        cur.close()
        conn.close()
        flash("Employee record added successfully.", "success")
        return redirect(url_for("records"))

    cur.close()
    conn.close()
    return render_template("record_form.html", employees=employees)

if __name__ == "__main__":
    app.run(debug=True)
