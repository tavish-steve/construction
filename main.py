from flask import Flask, render_template, request, redirect, url_for, flash
from psycopg2.extras import RealDictCursor
import psycopg2
import os
import logging
from datetime import datetime
from database import (
    init_db_pool,
    close_all_connections,
    init_employee_tables,
    get_clients,
    insert_clients,
    delete_clients_bulk as delete_clients_bulk_db,
    get_employees,
    insert_employees,
    get_employee_payments,
    insert_employee_payment,
    delete_employees_bulk as delete_employees_bulk_db,
    get_projects,
    insert_project,
    delete_projects_bulk as delete_projects_bulk_db,
    get_materials,
    insert_materials,
    delete_materials_bulk as delete_materials_bulk_db,
    get_payments,
    insert_payment,
    delete_payments_bulk as delete_payments_bulk_db,
    get_purchases,
    insert_purchases,
    get_purchase_items,
    insert_purchase_items,
    get_suppliers,
    insert_suppliers,
    delete_suppliers_bulk as delete_suppliers_bulk_db,
    get_projects_with_clients,
    get_project_materials,
    get_purchases_with_suppliers,
    get_purchase_details,
    get_payment_report,
    get_connection,
    return_connection,
    init_clients_table,
    init_suppliers_table,
    init_materials_table,
    init_projects_table,
    init_project_materials_table,
    init_purchases_table,
    init_purchase_items_table,
    init_payments_table
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

@app.before_request
def before_request():
    try:
        init_db_pool()
    except Exception as e:
        app.logger.error(f"Database pool initialization failed: {e}")

@app.route('/')
def index():
    return render_template('index.html', title='Home')

@app.route('/dashboard')
def dashboard():
    return redirect(url_for('index'))

@app.route('/clients')
def clients():
    clients = get_clients()
    return render_template('clients.html', title='Clients', clients=clients)

@app.route('/add_client', methods=['POST'])
def add_client():
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    address = request.form.get('address')
    if name:
        insert_clients((name, phone, email, address))
    return redirect(url_for('clients'))

@app.route('/delete_clients_bulk', methods=['POST'])
def delete_clients_bulk():
    client_ids = [int(cid) for cid in request.form.get('client_ids[]', '').split(',') if cid.isdigit()]
    if client_ids:
        delete_clients_bulk_db(client_ids)
    return redirect(url_for('clients'))

@app.route('/delete_employees_bulk', methods=['POST'])
def delete_employees_bulk():
    employee_ids = [int(eid) for eid in request.form.get('employee_ids[]', '').split(',') if eid.isdigit()]
    if employee_ids:
        delete_employees_bulk_db(employee_ids)
    return redirect(url_for('employees'))

@app.route('/employees')
def employees():
    employees = get_employees()
    return render_template('employees.html', title='Employees', employees=employees)

@app.route('/add_employee', methods=['POST'])
def add_employee():
    full_name = request.form.get('full_name')
    role = request.form.get('role')
    phone = request.form.get('phone')
    wage_per_day = request.form.get('wage_per_day')
    total_expected = request.form.get('total_expected')
    if full_name:
        wage_float = float(wage_per_day) if wage_per_day else 0.0
        total_float = float(total_expected) if total_expected else 0.0
        insert_employees((full_name, role, phone, wage_float, total_float))
    return redirect(url_for('employees'))

@app.route('/add_employee_payment', methods=['POST'])
def add_employee_payment():
    employee_id = request.form.get('employee_id')
    amount_paid = request.form.get('amount_paid')
    payment_date = request.form.get('payment_date')
    if employee_id and amount_paid:
        employee_id_int = int(employee_id)
        amount_float = float(amount_paid)
        insert_employee_payment((employee_id_int, amount_float, payment_date))
    return redirect(url_for('employees'))

@app.route('/projects')
def projects():
    projects = get_projects()
    clients = get_clients()
    return render_template('projects.html', title='Projects', projects=projects, clients=clients)

@app.route('/add_project', methods=['POST'])
def add_project():
    project_name = request.form.get('project_name')
    client_id = request.form.get('client_id')
    location = request.form.get('location')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    budget = request.form.get('budget')
    status = 'active'
    if project_name:
        client_id_int = int(client_id) if client_id else None
        budget_float = float(budget) if budget else 0.0
        insert_project((project_name, client_id_int, location, start_date, end_date, budget_float, status))
    return redirect(url_for('projects'))

@app.route('/delete_projects_bulk', methods=['POST'])
def delete_projects_bulk():
    project_ids = [int(pid) for pid in request.form.get('project_ids[]', '').split(',') if pid.isdigit()]
    if project_ids:
        delete_projects_bulk_db(project_ids)
    return redirect(url_for('projects'))

@app.route('/materials')
def materials():
    materials = get_materials()
    return render_template('materials.html', title='Materials', materials=materials)

@app.route('/add_material', methods=['POST'])
def add_material():
    material_name = request.form.get('material_name')
    unit = request.form.get('unit')
    unit_price = request.form.get('unit_price')
    stock_quantity = request.form.get('stock_quantity')
    if material_name:
        unit_price_float = float(unit_price) if unit_price else 0.0
        stock_int = int(stock_quantity) if stock_quantity else 0
        insert_materials((material_name, unit, unit_price_float, stock_int))
    return redirect(url_for('materials'))

@app.route('/delete_materials_bulk', methods=['POST'])
def delete_materials_bulk():
    material_ids = [int(mid) for mid in request.form.get('material_ids[]', '').split(',') if mid.isdigit()]
    if material_ids:
        delete_materials_bulk_db(material_ids)
    return redirect(url_for('materials'))

@app.route('/payments')
def payments():
    payments = get_payments()
    projects = get_projects()
    return render_template('payments.html', title='Payments', payments=payments, projects=projects)

@app.route('/add_payment', methods=['POST'])
def add_payment():
    project_id = request.form.get('project_id')
    amount_paid = request.form.get('amount_paid')
    payment_date = request.form.get('payment_date')
    method = request.form.get('method')
    if amount_paid:
        project_id_int = int(project_id) if project_id else None
        amount_float = float(amount_paid)
        insert_payment((project_id_int, amount_float, payment_date, method))
        flash(f'Payment of KSh {amount_paid} recorded successfully! <a href="{url_for("reports")}">View in Reports</a>', 'success')
    return redirect(url_for('payments'))

@app.route('/delete_payments_bulk', methods=['POST'])
def delete_payments_bulk():
    payment_ids = [int(pid) for pid in request.form.get('payment_ids[]', '').split(',') if pid.isdigit()]
    if payment_ids:
        delete_payments_bulk_db(payment_ids)
    return redirect(url_for('payments'))

@app.route('/purchases')
def purchases():
    purchases = get_purchases()
    suppliers = get_suppliers()
    materials = get_materials()
    return render_template('purchases.html', title='Purchases', purchases=purchases, suppliers=suppliers, materials=materials)

@app.route('/add_purchase', methods=['POST'])
def add_purchase():
    supplier_choice = request.form.get('supplier_choice')
    supplier_id = None
    if supplier_choice == 'new':
        new_supplier_name = request.form.get('new_supplier_name')
        new_supplier_phone = request.form.get('new_supplier_phone')
        new_supplier_email = request.form.get('new_supplier_email')
        if new_supplier_name:
            supplier_result = insert_suppliers((new_supplier_name, new_supplier_phone, new_supplier_email, ''))
            if supplier_result:
                supplier_id = supplier_result.get('supplier_id')
    else:
        supplier_id = request.form.get('supplier_id')
        supplier_id = int(supplier_id) if supplier_id else None
    material_id = request.form.get('material_id')
    quantity = request.form.get('quantity')
    unit_price = request.form.get('unit_price')
    if supplier_id and material_id and quantity and unit_price:
        material_id = int(material_id)
        quantity = int(quantity)
        unit_price = float(unit_price)
        total_amount = quantity * unit_price
        purchase_result = insert_purchases((supplier_id, total_amount))
        if purchase_result:
            purchase_id = purchase_result.get('purchase_id')
            insert_purchase_items((purchase_id, material_id, quantity, unit_price))
            flash(f'Purchase of KSh {total_amount} recorded successfully! <a href="{url_for("reports")}">View in Reports</a>', 'success')
    return redirect(url_for('purchases'))

@app.route('/delete_purchases_bulk', methods=['POST'])
def delete_purchases_bulk():
    purchase_ids = [int(pid) for pid in request.form.get('purchase_ids[]', '').split(',') if pid.isdigit()]
    if purchase_ids:
        delete_purchases_bulk_db(purchase_ids)
    return redirect(url_for('purchases'))

@app.route('/delete_suppliers_bulk', methods=['POST'])
def delete_suppliers_bulk():
    supplier_ids = [int(sid) for sid in request.form.get('supplier_ids[]', '').split(',') if sid.isdigit()]
    if supplier_ids:
        delete_suppliers_bulk_db(supplier_ids)
    return redirect(url_for('purchases'))

@app.route('/purchase-details')
def purchase_details_route():
    data = get_purchase_details()
    return render_template('purchase_details.html', title='Purchase Details', purchase_details=data)

@app.route('/reports')
def reports():
    projects_with_clients = get_projects_with_clients()
    project_materials = get_project_materials()
    purchases_with_suppliers = get_purchases_with_suppliers()
    purchase_details = get_purchase_details()
    payment_report = get_payment_report()
    return render_template(
        'reports.html',
        title='Reports',
        projects_with_clients=projects_with_clients,
        project_materials=project_materials,
        purchases_with_suppliers=purchases_with_suppliers,
        purchase_details=purchase_details,
        payment_report=payment_report
    )

if __name__ == '__main__':
    try:
        init_db_pool()
        init_employee_tables()
        init_clients_table()
        init_suppliers_table()
        init_materials_table()
        init_projects_table()
        init_project_materials_table()
        init_purchases_table()
        init_purchase_items_table()
        init_payments_table()
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    finally:
        close_all_connections()
