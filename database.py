import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connection pool settings
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'rty67jouj'),
    'database': os.environ.get('DB_NAME', 'construction_db')
}

# Initialize connection pool (None until first use)
connection_pool = None
_pool_initialized = False

def init_db_pool():
    """Initialize the database connection pool"""
    global connection_pool, _pool_initialized
    if connection_pool is None and not _pool_initialized:
        try:
            connection_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                **DB_CONFIG
            )
            _pool_initialized = True
            logger.info("Database connection pool initialized successfully!")
        except psycopg2.Error as e:
            logger.error(f"Error initializing database pool: {e}")
            connection_pool = None
    return connection_pool

def get_connection():
    """Get a connection from the pool with retry logic"""
    global connection_pool
    
    # Initialize pool if not exists
    if connection_pool is None:
        init_db_pool()
    
    if connection_pool is None:
        raise Exception("Database connection pool not available")
    
    # Retry logic for getting connection
    max_retries = 3
    retry_delay = 0.5
    
    for attempt in range(max_retries):
        try:
            conn = connection_pool.getconn()
            # Test the connection
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            return conn
        except psycopg2.Error as e:
            logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
            # Try to reinitialize pool on connection failure
            if connection_pool is not None:
                try:
                    connection_pool.closeall()
                except:
                    pass
                connection_pool = None
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay)
            else:
                raise e
    return None

def return_connection(conn):
    """Return a connection to the pool"""
    global connection_pool
    if conn and connection_pool:
        try:
            connection_pool.putconn(conn)
        except Exception as e:
            logger.warning(f"Error returning connection to pool: {e}")

def close_all_connections():
    """Close all connections in the pool"""
    global connection_pool, _pool_initialized
    if connection_pool:
        connection_pool.closeall()
        connection_pool = None
        _pool_initialized = False
        logger.info("Database connection pool closed")

def init_employee_tables():
    """Initialize employee-related tables and columns"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Create employees table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                employee_id SERIAL PRIMARY KEY,
                full_name VARCHAR(255) NOT NULL,
                role VARCHAR(100),
                phone VARCHAR(50),
                wage_per_day DECIMAL(10,2) DEFAULT 0,
                total_expected DECIMAL(10,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add created_at column if it doesn't exist (for existing tables)
        try:
            cur.execute("ALTER TABLE employees ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except:
            pass
            
        logger.info("Created employees table")
        
        # Create employee_payments table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS employee_payments (
                payment_id SERIAL PRIMARY KEY,
                employee_id INTEGER REFERENCES employees(employee_id),
                amount_paid DECIMAL(10,2) NOT NULL,
                payment_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("Created employee_payments table")
        
        cur.close()
    except psycopg2.Error as e:
        logger.error(f"Error initializing employee tables: {e}")
    finally:
        return_connection(conn)

# ============= CLIENTS =============
def get_clients():
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT client_id, name, phone, email, address, created_at FROM clients ORDER BY created_at DESC")
        result = cur.fetchall()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error getting clients: {e}")
        return []
    finally:
        return_connection(conn)

def insert_clients(values):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("INSERT INTO clients(name, phone, email, address) VALUES (%s, %s, %s, %s) RETURNING client_id", values)
        result = cur.fetchone()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error inserting client: {e}")
        return None
    finally:
        return_connection(conn)

# ============= EMPLOYEES =============
def get_employees():
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT 
                e.employee_id, 
                e.full_name, 
                e.role, 
                e.phone, 
                COALESCE(e.wage_per_day, 0) as wage_per_day,
                COALESCE(ep.total_paid, 0) as money_paid,
                COALESCE(e.total_expected, 0) - COALESCE(ep.total_paid, 0) as money_not_paid,
                e.created_at
            FROM employees e
            LEFT JOIN (
                SELECT employee_id, SUM(amount_paid) as total_paid
                FROM employee_payments
                GROUP BY employee_id
            ) ep ON e.employee_id = ep.employee_id
            ORDER BY e.employee_id DESC
        """)
        result = cur.fetchall()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error getting employees: {e}")
        return []
    finally:
        return_connection(conn)

def insert_employees(values):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("INSERT INTO employees(full_name, role, phone, wage_per_day, total_expected) VALUES (%s, %s, %s, %s, %s) RETURNING employee_id", values)
        result = cur.fetchone()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error inserting employee: {e}")
        return None
    finally:
        return_connection(conn)

# ============= EMPLOYEE PAYMENTS =============
def get_employee_payments():
    """Get all employee payments"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT ep.payment_id, ep.employee_id, e.full_name, ep.amount_paid, ep.payment_date
            FROM employee_payments ep
            LEFT JOIN employees e ON ep.employee_id = e.employee_id
            ORDER BY ep.payment_date DESC
        """)
        result = cur.fetchall()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error getting employee payments: {e}")
        return []
    finally:
        return_connection(conn)

def insert_employee_payment(values):
    """Insert a new employee payment"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("INSERT INTO employee_payments(employee_id, amount_paid, payment_date) VALUES (%s, %s, %s) RETURNING payment_id", values)
        result = cur.fetchone()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error inserting employee payment: {e}")
        return None
    finally:
        return_connection(conn)

# ============= PROJECTS =============
def get_projects():
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT p.project_id, p.project_name, c.name as client_name, p.location, 
                   p.start_date, p.end_date, p.budget, p.status
            FROM projects p
            LEFT JOIN clients c ON p.client_id = c.client_id
            ORDER BY p.project_id DESC
        """)
        result = cur.fetchall()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error getting projects: {e}")
        return []
    finally:
        return_connection(conn)

def insert_project(values):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            INSERT INTO projects(project_name, client_id, location, start_date, end_date, budget, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING project_id
        """, values)
        result = cur.fetchone()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error inserting project: {e}")
        return None
    finally:
        return_connection(conn)

# ============= MATERIALS =============
def get_materials():
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT material_id, material_name, unit, unit_price, stock_quantity FROM materials ORDER BY material_id DESC")
        result = cur.fetchall()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error getting materials: {e}")
        return []
    finally:
        return_connection(conn)

def insert_materials(values):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("INSERT INTO materials(material_name, unit, unit_price, stock_quantity) VALUES (%s, %s, %s, %s) RETURNING material_id", values)
        result = cur.fetchone()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error inserting material: {e}")
        return None
    finally:
        return_connection(conn)

# ============= SUPPLIERS =============
def get_suppliers():
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT supplier_id, supplier_name, phone, email, address FROM suppliers ORDER BY supplier_id DESC")
        result = cur.fetchall()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error getting suppliers: {e}")
        return []
    finally:
        return_connection(conn)

def insert_suppliers(values):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("INSERT INTO suppliers(supplier_name, phone, email, address) VALUES (%s, %s, %s, %s) RETURNING supplier_id", values)
        result = cur.fetchone()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error inserting supplier: {e}")
        return None
    finally:
        return_connection(conn)

# ============= PURCHASES =============
def get_purchases():
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT p.purchase_id, s.supplier_name, p.purchase_date, p.total_amount
            FROM purchases p
            LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
            ORDER BY p.purchase_date DESC
        """)
        result = cur.fetchall()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error getting purchases: {e}")
        return []
    finally:
        return_connection(conn)

def insert_purchases(values):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("INSERT INTO purchases(supplier_id, total_amount) VALUES (%s, %s) RETURNING purchase_id", values)
        result = cur.fetchone()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error inserting purchase: {e}")
        return None
    finally:
        return_connection(conn)

# ============= PURCHASE ITEMS =============
def get_purchase_items():
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT pi.purchase_item_id, pi.purchase_id, m.material_name, pi.quantity, pi.price
            FROM purchase_items pi
            LEFT JOIN materials m ON pi.material_id = m.material_id
            ORDER BY pi.purchase_item_id DESC
        """)
        result = cur.fetchall()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error getting purchase items: {e}")
        return []
    finally:
        return_connection(conn)

def insert_purchase_items(values):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("INSERT INTO purchase_items(purchase_id, material_id, quantity, price) VALUES (%s, %s, %s, %s) RETURNING purchase_item_id", values)
        result = cur.fetchone()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error inserting purchase item: {e}")
        return None
    finally:
        return_connection(conn)

# ============= PAYMENTS =============
def get_payments():
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT pay.payment_id, pr.project_name, c.name as client_name, pay.amount_paid, 
                   pay.payment_date, pay.method
            FROM payments pay
            LEFT JOIN projects pr ON pay.project_id = pr.project_id
            LEFT JOIN clients c ON pr.client_id = c.client_id
            ORDER BY pay.payment_date DESC
        """)
        result = cur.fetchall()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error getting payments: {e}")
        return []
    finally:
        return_connection(conn)

def insert_payment(values):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("INSERT INTO payments(project_id, amount_paid, payment_date, method) VALUES (%s, %s, %s, %s) RETURNING payment_id", values)
        result = cur.fetchone()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error inserting payment: {e}")
        return None
    finally:
        return_connection(conn)

# ============= REPORTS (JOIN QUERIES) =============

def get_projects_with_clients():
    """Get all projects with client information"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT 
                p.project_id,
                p.project_name,
                c.name AS client_name,
                p.location,
                p.budget,
                p.status,
                p.start_date,
                p.end_date
            FROM projects p
            LEFT JOIN clients c ON p.client_id = c.client_id
            ORDER BY p.project_id DESC
        """)
        result = cur.fetchall()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error getting projects with clients: {e}")
        return []
    finally:
        return_connection(conn)

def get_project_materials():
    """Get materials used in projects"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT
                pr.project_name,
                m.material_name,
                pm.quantity_used,
                pm.used_on
            FROM project_materials pm
            LEFT JOIN projects pr ON pm.project_id = pr.project_id
            LEFT JOIN materials m ON pm.material_id = m.material_id
            ORDER BY pr.project_name
        """)
        result = cur.fetchall()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error getting project materials: {e}")
        return []
    finally:
        return_connection(conn)

def get_purchases_with_suppliers():
    """Get purchases with supplier information"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT
                p.purchase_id,
                s.supplier_name,
                p.purchase_date,
                p.total_amount,
                p.status
            FROM purchases p
            LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
            ORDER BY p.purchase_date DESC
        """)
        result = cur.fetchall()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error getting purchases with suppliers: {e}")
        return []
    finally:
        return_connection(conn)

def get_purchase_details():
    """Get detailed purchase information with supplier and material details"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT
                s.supplier_name,
                m.material_name,
                pi.quantity,
                pi.price,
                p.purchase_date,
                p.purchase_id
            FROM purchase_items pi
            LEFT JOIN purchases p ON pi.purchase_id = p.purchase_id
            LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
            LEFT JOIN materials m ON pi.material_id = m.material_id
            ORDER BY p.purchase_date DESC
        """)
        result = cur.fetchall()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error getting purchase details: {e}")
        return []
    finally:
        return_connection(conn)

def get_payment_report():
    """Get payment report with project and client details"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT
                pay.payment_id,
                c.name AS client_name,
                pr.project_name,
                pay.amount_paid,
                pay.payment_date,
                pay.method,
                pay.status
            FROM payments pay
            LEFT JOIN projects pr ON pay.project_id = pr.project_id
            LEFT JOIN clients c ON pr.client_id = c.client_id
            ORDER BY pay.payment_date DESC
        """)
        result = cur.fetchall()
        cur.close()
        return result
    except psycopg2.Error as e:
        logger.error(f"Error getting payment report: {e}")
        return []
    finally:
        return_connection(conn)

# ============= DISPLAY FUNCTIONS =============

def display_projects_with_clients():
    """Display projects with client information"""
    print("\n" + "="*80)
    print("PROJECTS WITH CLIENTS")
    print("="*80)
    data = get_projects_with_clients()
    for row in data:
        print(f"ID: {row['project_id']}, Project: {row['project_name']}, Client: {row['client_name']}, Location: {row['location']}, Budget: {row['budget']}, Status: {row['status']}")
    return data

def display_project_materials():
    """Display project materials usage"""
    print("\n" + "="*80)
    print("PROJECT MATERIALS")
    print("="*80)
    data = get_project_materials()
    for row in data:
        print(f"Project: {row['project_name']}, Material: {row['material_name']}, Quantity: {row['quantity_used']}, Used On: {row['used_on']}")
    return data

def display_purchases_with_suppliers():
    """Display purchases with supplier information"""
    print("\n" + "="*80)
    print("PURCHASES WITH SUPPLIERS")
    print("="*80)
    data = get_purchases_with_suppliers()
    for row in data:
        print(f"Purchase ID: {row['purchase_id']}, Supplier: {row['supplier_name']}, Date: {row['purchase_date']}, Total: {row['total_amount']}")
    return data

def display_purchase_details():
    """Display detailed purchase information"""
    print("\n" + "="*80)
    print("PURCHASE DETAILS")
    print("="*80)
    data = get_purchase_details()
    for row in data:
        print(f"Supplier: {row['supplier_name']}, Material: {row['material_name']}, Quantity: {row['quantity']}, Price: {row['price']}, Date: {row['purchase_date']}")
    return data

def display_payment_report():
    """Display payment report"""
    print("\n" + "="*80)
    print("PAYMENT REPORT")
    print("="*80)
    data = get_payment_report()
    for row in data:
        print(f"Client: {row['client_name']}, Project: {row['project_name']}, Amount: {row['amount_paid']}, Date: {row['payment_date']}, Method: {row['method']}")
    return data

def display_all_data():
    """Display all fetched data in a readable format"""
    print("\n" + "="*50)
    print("CLIENTS")
    print("="*50)
    clients = get_clients()
    for client in clients:
        print(f"ID: {client['client_id']}, Name: {client['name']}, Phone: {client['phone']}, Email: {client['email']}, Address: {client['address']}")
    
    print("\n" + "="*50)
    print("PROJECTS")
    print("="*50)
    projects = get_projects()
    for project in projects:
        print(f"ID: {project['project_id']}, Name: {project['project_name']}, Client: {project['client_name']}, Location: {project['location']}, Budget: {project['budget']}, Status: {project['status']}")
    
    print("\n" + "="*50)
    print("MATERIALS")
    print("="*50)
    materials = get_materials()
    for material in materials:
        print(f"ID: {material['material_id']}, Name: {material['material_name']}, Unit: {material['unit']}, Unit Price: {material['unit_price']}, Stock: {material['stock_quantity']}")
    
    print("\n" + "="*50)
    print("EMPLOYEES")
    print("="*50)
    employees = get_employees()
    for employee in employees:
        print(f"ID: {employee['employee_id']}, Name: {employee['full_name']}, Role: {employee['role']}, Phone: {employee['phone']}, Salary: {employee['salary']}")
    
    print("\n" + "="*50)
    print("SUPPLIERS")
    print("="*50)
    suppliers = get_suppliers()
    for supplier in suppliers:
        print(f"ID: {supplier['supplier_id']}, Name: {supplier['supplier_name']}, Phone: {supplier['phone']}, Email: {supplier['email']}, Address: {supplier['address']}")
    
    print("\n" + "="*50)
    print("PURCHASES")
    print("="*50)
    purchases = get_purchases()
    for purchase in purchases:
        print(f"ID: {purchase['purchase_id']}, Supplier: {purchase['supplier_name']}, Date: {purchase['purchase_date']}, Total: {purchase['total_amount']}")
    
    print("\n" + "="*50)
    print("PAYMENTS")
    print("="*50)
    payments = get_payments()
    for payment in payments:
        print(f"ID: {payment['payment_id']}, Project: {payment['project_name']}, Client: {payment['client_name']}, Amount: {payment['amount_paid']}, Date: {payment['payment_date']}, Method: {payment['method']}")

def display_all_reports():
    """Display all reports"""
    display_projects_with_clients()
    display_project_materials()
    display_purchases_with_suppliers()
    display_purchase_details()
    display_payment_report()

# Test connection and display data
if __name__ == "__main__":
    # Initialize the pool first
    init_db_pool()
    print("Database connection successful!")
    display_all_data()
    # Close pool when done
    close_all_connections()
