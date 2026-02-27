# Construction Management System

A web-based construction management application built with Flask and PostgreSQL. This system helps manage construction projects, clients, employees, materials, suppliers, purchases, and payments.

## Table of Contents

- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Features](#features)
- [Database Schema](#database-schema)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Application Routes](#application-routes)
- [Database Functions](#database-functions)

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Python Flask |
| **Database** | PostgreSQL |
| **Database Driver** | psycopg2 |
| **Frontend** | HTML5, Bootstrap 5 |
| **Data Tables** | DataTables (jQuery plugin) |
| **templating** | Jinja2 |

---

## Project Structure

```
construction/
├── main.py                 # Flask application entry point and routes
├── database.py             # Database connection pool and CRUD operations
├── static/
│   └── navbar.css          # Custom navbar styles
├── templates/             # HTML Jinja2 templates
│   ├── base.html          # Base template with navigation
│   ├── index.html         # Home/dashboard page
│   ├── clients.html       # Client management
│   ├── employees.html     # Employee management
│   ├── projects.html      # Project management
│   ├── materials.html     # Materials inventory
│   ├── purchases.html     # Purchase management
│   ├── purchase_details.html  # Purchase details view
│   ├── payments.html      # Payment tracking
│   └── reports.html       # Reports/dashboard view
└── README.md              # This file
```

---

## Features

### 1. Client Management
- Add new clients with name, phone, email, and address
- View all clients in a searchable data table
- Edit and delete client information

### 2. Employee Management
- Track employee details (name, role, phone, salary)
- View employee list with filtering capabilities
- Add new employees to the system

### 3. Project Management
- Create projects linked to clients
- Track project details (location, start/end dates, budget, status)
- View all projects with client association

### 4. Materials Inventory
- Manage construction materials catalog
- Track unit prices and stock quantities
- View material inventory with pricing

### 5. Supplier Management
- Add suppliers during purchase creation
- Track supplier contact information
- Link purchases to suppliers

### 6. Purchase Management
- Create purchases from suppliers
- Add multiple materials to a single purchase
- Track purchase totals and dates

### 7. Payment Tracking
- Record payments received from clients
- Link payments to specific projects
- Track payment methods and dates

### 8. Reports Dashboard
- View all projects with client details
- Track materials used per project
- View purchases with supplier information
- Payment summary reports

---

## Database Schema

### Tables

| Table | Description |
|-------|-------------|
| `clients` | Customer/client information |
| `employees` | Staff member details |
| `projects` | Construction projects linked to clients |
| `materials` | Material inventory |
| `suppliers` | Material suppliers/vendors |
| `purchases` | Purchase orders from suppliers |
| `purchase_items` | Individual items in a purchase |
| `payments` | Payments received from clients |
| `project_materials` | Materials assigned to projects |

### Database Configuration

The application connects to PostgreSQL using the following default configuration:

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'user': 'postgres',
    'password': 'rty67jouj',
    'database': 'construction_db'
}
```

---

## Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher

### 1. Install Python Dependencies

```bash
pip install flask psycopg2-binary
```

### 2. Set Up PostgreSQL Database

```sql
CREATE DATABASE construction_db;
```

### 3. Create Database Tables

You'll need to create the following tables in your PostgreSQL database:

```sql
-- Clients table
CREATE TABLE clients (
    client_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Employees table
CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(100),
    phone VARCHAR(50),
    salary DECIMAL(10, 2)
);

-- Projects table
CREATE TABLE projects (
    project_id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    client_id INTEGER REFERENCES clients(client_id),
    location VARCHAR(255),
    start_date DATE,
    end_date DATE,
    budget DECIMAL(12, 2),
    status VARCHAR(50) DEFAULT 'active'
);

-- Materials table
CREATE TABLE materials (
    material_id SERIAL PRIMARY KEY,
    material_name VARCHAR(255) NOT NULL,
    unit VARCHAR(50),
    unit_price DECIMAL(10, 2),
    stock_quantity INTEGER
);

-- Suppliers table
CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT
);

-- Purchases table
CREATE TABLE purchases (
    purchase_id SERIAL PRIMARY KEY,
    supplier_id INTEGER REFERENCES suppliers(supplier_id),
    purchase_date DATE DEFAULT CURRENT_DATE,
    total_amount DECIMAL(12, 2),
    status VARCHAR(50) DEFAULT 'pending'
);

-- Purchase Items table
CREATE TABLE purchase_items (
    purchase_item_id SERIAL PRIMARY KEY,
    purchase_id INTEGER REFERENCES purchases(purchase_id),
    material_id INTEGER REFERENCES materials(material_id),
    quantity INTEGER,
    price DECIMAL(10, 2)
);

-- Payments table
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(project_id),
    amount_paid DECIMAL(12, 2),
    payment_date DATE,
    method VARCHAR(50),
    status VARCHAR(50) DEFAULT 'completed'
);

-- Project Materials table
CREATE TABLE project_materials (
    project_material_id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(project_id),
    material_id INTEGER REFERENCES materials(material_id),
    quantity_used INTEGER,
    used_on DATE
);
```

---

## Configuration

### Environment Variables

You can override database configuration using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | localhost | Database host |
| `DB_PORT` | 5432 | Database port |
| `DB_USER` | postgres | Database username |
| `DB_PASSWORD` | rty67jouj | Database password |
| `DB_NAME` | construction_db | Database name |

### Example: Setting Environment Variables

**Windows (CMD):**
```cmd
set DB_HOST=localhost
set DB_PORT=5432
set DB_USER=myuser
set DB_PASSWORD=mypassword
set DB_NAME=construction_db
```

**Linux/Mac:**
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=myuser
export DB_PASSWORD=mypassword
export DB_NAME=construction_db
```

---

## Running the Application

### Start the Development Server

```bash
python main.py
```

The application will start on `http://localhost:5000` by default.

### Access the Application

Open your web browser and navigate to:
```
http://localhost:5000
```

---

## Application Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Dashboard/Reports (home page) |
| `/clients` | GET | View all clients |
| `/add_client` | POST | Add new client |
| `/employees` | GET | View all employees |
| `/add_employee` | POST | Add new employee |
| `/projects` | GET | View all projects |
| `/add_project` | POST | Add new project |
| `/materials` | GET | View all materials |
| `/add_material` | POST | Add new material |
| `/purchases` | GET | View all purchases |
| `/add_purchase` | POST | Add new purchase |
| `/purchase-details` | GET | View purchase details |
| `/payments` | GET | View all payments |
| `/add_payment` | POST | Add new payment |
| `/reports` | GET | View all reports |

---

## Database Functions

### Connection Management

| Function | Description |
|----------|-------------|
| [`init_db_pool()`](database.py:24) | Initialize PostgreSQL connection pool |
| [`get_connection()`](database.py:41) | Get connection from pool with retry logic |
| [`return_connection()`](database.py:81) | Return connection to pool |
| [`close_all_connections()`](database.py:90) | Close all pool connections |

### Client Functions

| Function | Description |
|----------|-------------|
| [`get_clients()`](database.py:100) | Retrieve all clients |
| [`insert_clients()`](database.py:115) | Add new client |

### Employee Functions

| Function | Description |
|----------|-------------|
| [`get_employees()`](database.py:131) | Retrieve all employees |
| [`insert_employees()`](database.py:146) | Add new employee |

### Project Functions

| Function | Description |
|----------|-------------|
| [`get_projects()`](database.py:162) | Retrieve all projects with client info |
| [`insert_project()`](database.py:183) | Add new project |
| [`get_projects_with_clients()`](database.py:375) | Get projects joined with clients |

### Material Functions

| Function | Description |
|----------|-------------|
| [`get_materials()`](database.py:202) | Retrieve all materials |
| [`insert_materials()`](database.py:217) | Add new material |
| [`get_project_materials()`](database.py:404) | Get materials used in projects |

### Supplier Functions

| Function | Description |
|----------|-------------|
| [`get_suppliers()`](database.py:233) | Retrieve all suppliers |
| [`insert_suppliers()`](database.py:248) | Add new supplier |

### Purchase Functions

| Function | Description |
|----------|-------------|
| [`get_purchases()`](database.py:264) | Retrieve all purchases |
| [`insert_purchases()`](database.py:284) | Add new purchase |
| [`get_purchase_items()`](database.py:300) | Retrieve purchase line items |
| [`insert_purchase_items()`](database.py:320) | Add purchase line item |
| [`get_purchases_with_suppliers()`](database.py:430) | Get purchases with supplier info |
| [`get_purchase_details()`](database.py:456) | Get detailed purchase information |

### Payment Functions

| Function | Description |
|----------|-------------|
| [`get_payments()`](database.py:336) | Retrieve all payments |
| [`insert_payment()`](database.py:358) | Add new payment |
| [`get_payment_report()`](database.py:485) | Get payment report with project/client details |

---

## Troubleshooting

### Database Connection Issues

If you encounter database connection errors:

1. Verify PostgreSQL is running
2. Check database credentials in [`database.py`](database.py:12)
3. Ensure the database exists: `SELECT 1 FROM pg_database WHERE datname='construction_db'`

### Common Errors

| Error | Solution |
|-------|----------|
| `psycopg2.OperationalError` | Check PostgreSQL is running and credentials are correct |
| `connection pool not available` | Ensure `init_db_pool()` is called before requests |
| `relation "tablename" does not` | Create the required database tables |

---

## License

This project is provided as-is for construction management purposes.

---

## Author

Construction Management System
