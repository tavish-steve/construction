from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from psycopg2.extras import RealDictCursor
import psycopg2
import os
import logging
from datetime import datetime
from database import (
    init_db_pool,
    close_all_connections,
    init_employee_tables,
    init_users_table,
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
    init_payments_table,
    get_user_by_username,
    get_user_by_id,
    get_all_users,
    insert_user,
    delete_user,
    update_user_role,
    change_user_password
)
import bcrypt
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User:
    def __init__(self, user_id, username, role):
        self.id = user_id
        self.username = username
        self.role = role
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
    
    def is_super_admin(self):
        return self.role == 'super_admin'
    
    def is_admin(self):
        return self.role in ['super_admin', 'admin']

@login_manager.user_loader
def load_user(user_id):
    user = get_user_by_id(int(user_id))
    if user:
        return User(user['user_id'], user['username'], user['role'])
    return None

def create_super_admin():
    """Create default super admin user if none exists"""
    conn = None
    try:
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if not admin_password:
            logger.warning("ADMIN_PASSWORD not set in environment. Skipping default super admin creation.")
            return
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT user_id FROM users WHERE role = 'super_admin'")
        if not cur.fetchone():
            password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin_username = os.environ.get('ADMIN_USERNAME', 'superadmin')
            cur.execute("INSERT INTO users(username, password_hash, role) VALUES (%s, %s, %s)", (admin_username, password_hash, 'super_admin'))
            conn.commit()
            logger.info(f"Created super admin user: {admin_username}")
        cur.close()
    except psycopg2.Error as e:
        logger.error(f"Error creating super admin: {e}")
    finally:
        return_connection(conn)

def initialize_database():
    try:
        init_db_pool()
        init_users_table()
        init_employee_tables()
        init_clients_table()
        init_suppliers_table()
        init_materials_table()
        init_projects_table()
        init_project_materials_table()
        init_purchases_table()
        init_purchase_items_table()
        init_payments_table()
        create_super_admin()
    except Exception as e:
        app.logger.error(f"Database initialization failed: {e}")


initialize_database()

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

@app.before_request
def before_request():
    try:
        init_db_pool()
    except Exception as e:
        app.logger.error(f"Database pool initialization failed: {e}")
    
    exempt_routes = ['login', 'static']
    if not current_user.is_authenticated and request.endpoint not in exempt_routes and not request.path.startswith('/static'):
        return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html', title='Home')

@app.route('/dashboard')
@login_required
def dashboard():
    return redirect(url_for('index'))

@app.route('/clients')
@login_required
def clients():
    clients = get_clients()
    return render_template('clients.html', title='Clients', clients=clients)

@app.route('/add_client', methods=['POST'])
@login_required
def add_client():
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    address = request.form.get('address')
    if name:
        insert_clients((name, phone, email, address))
    return redirect(url_for('clients'))

@app.route('/delete_clients_bulk', methods=['POST'])
@login_required
def delete_clients_bulk():
    client_ids = [int(cid) for cid in request.form.get('client_ids[]', '').split(',') if cid.isdigit()]
    if client_ids:
        delete_clients_bulk_db(client_ids)
    return redirect(url_for('clients'))

@app.route('/delete_employees_bulk', methods=['POST'])
@login_required
def delete_employees_bulk():
    employee_ids = [int(eid) for eid in request.form.get('employee_ids[]', '').split(',') if eid.isdigit()]
    if employee_ids:
        delete_employees_bulk_db(employee_ids)
    return redirect(url_for('employees'))

@app.route('/employees')
@login_required
def employees():
    employees = get_employees()
    return render_template('employees.html', title='Employees', employees=employees)

@app.route('/add_employee', methods=['POST'])
@login_required
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
@login_required
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
@login_required
def projects():
    projects = get_projects()
    clients = get_clients()
    return render_template('projects.html', title='Projects', projects=projects, clients=clients)

@app.route('/add_project', methods=['POST'])
@login_required
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
@login_required
def delete_projects_bulk():
    project_ids = [int(pid) for pid in request.form.get('project_ids[]', '').split(',') if pid.isdigit()]
    if project_ids:
        delete_projects_bulk_db(project_ids)
    return redirect(url_for('projects'))

@app.route('/materials')
@login_required
def materials():
    materials = get_materials()
    return render_template('materials.html', title='Materials', materials=materials)

@app.route('/add_material', methods=['POST'])
@login_required
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
@login_required
def delete_materials_bulk():
    material_ids = [int(mid) for mid in request.form.get('material_ids[]', '').split(',') if mid.isdigit()]
    if material_ids:
        delete_materials_bulk_db(material_ids)
    return redirect(url_for('materials'))

@app.route('/payments')
@login_required
def payments():
    payments = get_payments()
    projects = get_projects()
    return render_template('payments.html', title='Payments', payments=payments, projects=projects)

@app.route('/add_payment', methods=['POST'])
@login_required
def add_payment():
    project_id = request.form.get('project_id')
    amount_paid = request.form.get('amount_paid')
    payment_date = request.form.get('payment_date')
    method = request.form.get('method')
    if amount_paid:
        project_id_int = int(project_id) if project_id else None
        amount_float = float(amount_paid)
        insert_payment((project_id_int, amount_float, payment_date, method))
        flash(f'Payment of KSh {amount_paid} recorded successfully! <a href="{url_for("reports")}"></a>', 'success')
    return redirect(url_for('payments'))

@app.route('/delete_payments_bulk', methods=['POST'])
@login_required
def delete_payments_bulk():
    payment_ids = [int(pid) for pid in request.form.get('payment_ids[]', '').split(',') if pid.isdigit()]
    if payment_ids:
        delete_payments_bulk_db(payment_ids)
    return redirect(url_for('payments'))

@app.route('/purchases')
@login_required
def purchases():
    purchases = get_purchases()
    suppliers = get_suppliers()
    materials = get_materials()
    return render_template('purchases.html', title='Purchases', purchases=purchases, suppliers=suppliers, materials=materials)

@app.route('/add_purchase', methods=['POST'])
@login_required
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
@login_required
def delete_purchases_bulk():
    purchase_ids = [int(pid) for pid in request.form.get('purchase_ids[]', '').split(',') if pid.isdigit()]
    if purchase_ids:
        delete_purchases_bulk_db(purchase_ids)
    return redirect(url_for('purchases'))

@app.route('/delete_suppliers_bulk', methods=['POST'])
@login_required
def delete_suppliers_bulk():
    supplier_ids = [int(sid) for sid in request.form.get('supplier_ids[]', '').split(',') if sid.isdigit()]
    if supplier_ids:
        delete_suppliers_bulk_db(supplier_ids)
    return redirect(url_for('purchases'))

@app.route('/purchase-details')
@login_required
def purchase_details_route():
    data = get_purchase_details()
    return render_template('purchase_details.html', title='Purchase Details', purchase_details=data)

@app.route('/reports')
@login_required
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = get_user_by_username(username)
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            login_user(User(user['user_id'], user['username'], user['role']))
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', title='Login')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_super_admin():
        flash('Access denied. Super admin only.', 'danger')
        return redirect(url_for('index'))
    users = get_all_users()
    return render_template('admin_users.html', title='User Management', users=users)

@app.route('/admin/users/add', methods=['POST'])
@login_required
def admin_add_user():
    if not current_user.is_super_admin():
        flash('Access denied. Super admin only.', 'danger')
        return redirect(url_for('admin_users'))
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role', 'user')
    if username and password:
        existing = get_user_by_username(username)
        if existing:
            flash('Username already exists', 'danger')
        else:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            insert_user(username, password_hash, role)
            flash(f'User {username} created successfully', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_super_admin():
        flash('Access denied. Super admin only.', 'danger')
        return redirect(url_for('index'))
    user = get_user_by_id(user_id)
    if user and user['role'] == 'super_admin':
        flash('Cannot delete super admin', 'danger')
    else:
        delete_user(user_id)
        flash('User deleted successfully', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/update_role/<int:user_id>', methods=['POST'])
@login_required
def admin_update_user_role(user_id):
    if not current_user.is_super_admin():
        flash('Access denied. Super admin only.', 'danger')
        return redirect(url_for('index'))
    new_role = request.form.get('role')
    user = get_user_by_id(user_id)
    if user and user['role'] != 'super_admin':
        update_user_role(user_id, new_role)
        flash('User role updated', 'success')
    else:
        flash('Cannot change super admin role', 'danger')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/change_password/<int:user_id>', methods=['POST'])
@login_required
def admin_change_password(user_id):
    if not current_user.is_super_admin():
        flash('Access denied. Super admin only.', 'danger')
        return redirect(url_for('index'))
    user = get_user_by_id(user_id)
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin_users'))
    if user['role'] == 'super_admin':
        flash('Cannot change super admin password here. Use "Change My Password" instead.', 'danger')
        return redirect(url_for('admin_users'))
    new_password = request.form.get('new_password')
    if new_password and len(new_password) >= 8:
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        change_user_password(user_id, password_hash)
        flash(f'Password changed for {user["username"]}', 'success')
    else:
        flash('Password must be at least 8 characters', 'danger')
    return redirect(url_for('admin_users'))

@app.route('/admin/change_own_password', methods=['POST'])
@login_required
def admin_change_own_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    if not current_password or not new_password or not confirm_password:
        flash('All fields are required', 'danger')
    elif new_password != confirm_password:
        flash('New passwords do not match', 'danger')
    elif len(new_password) < 8:
        flash('Password must be at least 8 characters', 'danger')
    else:
        user = get_user_by_id(current_user.id)
        if bcrypt.checkpw(current_password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            change_user_password(current_user.id, password_hash)
            flash('Password changed successfully', 'success')
        else:
            flash('Current password is incorrect', 'danger')
    return redirect(url_for('admin_users'))

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
