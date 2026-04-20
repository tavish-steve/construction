from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from psycopg2.extras import RealDictCursor
import psycopg2
import bcrypt
import os
import logging
from database import (
    init_db_pool,
    close_all_connections,
    init_employee_tables,
    init_admin_table,
    get_admin_user,
    create_admin_user,
    get_clients,
    insert_clients,
    get_employees,
    insert_employees,
    get_employee_payments,
    insert_employee_payment,
    get_projects,
    insert_project,
    get_materials,
    insert_materials,
    get_payments,
    insert_payment,
    get_purchases,
    insert_purchases,
    get_purchase_items,
    insert_purchase_items,
    get_suppliers,
    insert_suppliers,
    get_projects_with_clients,
    get_project_materials,
    get_purchases_with_suppliers,
    get_purchase_details,
    get_payment_report,
    get_connection,
    return_connection
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id, password_hash):
        self.id = user_id
        self.password_hash = password_hash

@login_manager.user_loader
def load_user(user_id):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, password_hash FROM admin_users WHERE id = %s", (user_id,))
        result = cur.fetchone()
        cur.close()
        if result:
            return User(result['id'], result['password_hash'])
    except Exception as e:
        app.logger.error(f"Error loading user: {e}")
    finally:
        return_connection(conn)
    return None

# ============= AUTHENTICATION =============
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    error = None
    if request.method == 'POST':
        password = request.form.get('password')
        
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT id, password_hash FROM admin_users LIMIT 1")
            result = cur.fetchone()
            cur.close()
            
            if result and bcrypt.checkpw(password.encode('utf-8'), result['password_hash'].encode('utf-8')):
                user = User(result['id'], result['password_hash'])
                login_user(user)
                flash('Logged in successfully!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                error = 'Invalid password'
        except Exception as e:
            app.logger.error(f"Login error: {e}")
            error = 'Invalid password'
        finally:
            return_connection(conn)
    
    return render_template('login.html', title='Login', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Initialize database connection pool before first request
@app.before_request
def before_request():
    """Ensure database pool is initialized before each request"""
    try:
        init_db_pool()
    except Exception as e:
        app.logger.error(f"Database pool initialization failed: {e}")

# Home - Company Info Page
@app.route('/')
def index():
    """Display login page first"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('index.html', title='Home')

# Dashboard route (alias for home)
@app.route('/dashboard')
@login_required
def dashboard():
    """Display the dashboard - same as home page"""
    return redirect(url_for('index'))

# Clients
@app.route('/clients')
@login_required
def clients():
    """Display all clients"""
    clients = get_clients()
    return render_template('clients.html', title='Clients', clients=clients)

@app.route('/add_client', methods=['POST'])
@login_required
def add_client():
    """Add a new client"""
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    address = request.form.get('address')
    
    if name:
        insert_clients((name, phone, email, address))
    
    return redirect(url_for('clients'))

# Employees
@app.route('/employees')
@login_required
def employees():
    """Display all employees"""
    employees = get_employees()
    return render_template('employees.html', title='Employees', employees=employees)

@app.route('/add_employee', methods=['POST'])
@login_required
def add_employee():
    """Add a new employee"""
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
    """Record a payment to an employee"""
    employee_id = request.form.get('employee_id')
    amount_paid = request.form.get('amount_paid')
    payment_date = request.form.get('payment_date')
    
    if employee_id and amount_paid:
        employee_id_int = int(employee_id)
        amount_float = float(amount_paid)
        insert_employee_payment((employee_id_int, amount_float, payment_date))
    
    return redirect(url_for('employees'))

# Projects
@app.route('/projects')
@login_required
def projects():
    """Display projects with client information"""
    projects = get_projects()
    clients = get_clients()
    return render_template('projects.html', title='Projects', projects=projects, clients=clients)

@app.route('/add_project', methods=['POST'])
@login_required
def add_project():
    """Add a new project"""
    project_name = request.form.get('project_name')
    client_id = request.form.get('client_id')
    location = request.form.get('location')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    budget = request.form.get('budget')
    status = 'active'  # Default status
    
    if project_name:
        client_id_int = int(client_id) if client_id else None
        budget_float = float(budget) if budget else 0.0
        insert_project((project_name, client_id_int, location, start_date, end_date, budget_float, status))
    
    return redirect(url_for('projects'))

# Materials
@app.route('/materials')
@login_required
def materials():
    """Display all materials"""
    materials = get_materials()
    return render_template('materials.html', title='Materials', materials=materials)

@app.route('/add_material', methods=['POST'])
@login_required
def add_material():
    """Add a new material"""
    material_name = request.form.get('material_name')
    unit = request.form.get('unit')
    unit_price = request.form.get('unit_price')
    stock_quantity = request.form.get('stock_quantity')
    
    if material_name:
        unit_price_float = float(unit_price) if unit_price else 0.0
        stock_int = int(stock_quantity) if stock_quantity else 0
        insert_materials((material_name, unit, unit_price_float, stock_int))
    
    return redirect(url_for('materials'))

# Payments
@app.route('/payments')
@login_required
def payments():
    """Display payment report"""
    payments = get_payments()
    projects = get_projects()
    return render_template('payments.html', title='Payments', payments=payments, projects=projects)

@app.route('/add_payment', methods=['POST'])
@login_required
def add_payment():
    """Add a new payment"""
    project_id = request.form.get('project_id')
    amount_paid = request.form.get('amount_paid')
    payment_date = request.form.get('payment_date')
    method = request.form.get('method')
    
    if amount_paid:
        project_id_int = int(project_id) if project_id else None
        amount_float = float(amount_paid)
        insert_payment((project_id_int, amount_float, payment_date, method))
    
    return redirect(url_for('payments'))

# Purchases
@app.route('/purchases')
@login_required
def purchases():
    """Display purchases with suppliers"""
    purchases = get_purchases()
    suppliers = get_suppliers()
    materials = get_materials()
    return render_template('purchases.html', title='Purchases', purchases=purchases, suppliers=suppliers, materials=materials)

@app.route('/add_purchase', methods=['POST'])
@login_required
def add_purchase():
    """Add a new purchase with optional new supplier and material"""
    supplier_choice = request.form.get('supplier_choice')
    
    supplier_id = None
    
    if supplier_choice == 'new':
        # Create new supplier
        new_supplier_name = request.form.get('new_supplier_name')
        new_supplier_phone = request.form.get('new_supplier_phone')
        new_supplier_email = request.form.get('new_supplier_email')
        
        if new_supplier_name:
            supplier_result = insert_suppliers((new_supplier_name, new_supplier_phone, new_supplier_email, ''))
            if supplier_result:
                supplier_id = supplier_result.get('supplier_id')
    else:
        # Use existing supplier
        supplier_id = request.form.get('supplier_id')
        supplier_id = int(supplier_id) if supplier_id else None
    
    # Get material and purchase details
    material_id = request.form.get('material_id')
    quantity = request.form.get('quantity')
    unit_price = request.form.get('unit_price')
    
    if supplier_id and material_id and quantity and unit_price:
        material_id = int(material_id)
        quantity = int(quantity)
        unit_price = float(unit_price)
        total_amount = quantity * unit_price
        
        # Insert purchase
        purchase_result = insert_purchases((supplier_id, total_amount))
        
        if purchase_result:
            purchase_id = purchase_result.get('purchase_id')
            # Insert purchase item
            insert_purchase_items((purchase_id, material_id, quantity, unit_price))
    
    return redirect(url_for('purchases'))

# Purchase Details
@app.route('/purchase-details')
@login_required
def purchase_details_route():
    """Display detailed purchase information"""
    data = get_purchase_details()
    return render_template('purchase_details.html', title='Purchase Details', purchase_details=data)

# Reports
@app.route('/reports')
@login_required
def reports():
    """Display all reports"""
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
        # Initialize pool before running
        init_db_pool()
        # Initialize employee tables
        init_employee_tables()
        # Initialize admin table and create default admin if needed
        init_admin_table()
        admin = get_admin_user()
        if not admin:
            create_admin_user('admin', 'admin123')
            logger.info("Created default admin user")
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    finally:
        # Clean up connection pool on shutdown
        close_all_connections()
