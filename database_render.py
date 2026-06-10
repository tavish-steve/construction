

from database import (
    close_all_connections,
    init_db_pool,
    init_employee_tables,
    init_clients_table,
    init_suppliers_table,
    init_materials_table,
    init_projects_table,
    init_project_materials_table,
    init_purchases_table,
    init_purchase_items_table,
    init_payments_table,
)


def bootstrap_database():
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


if __name__ == "__main__":
    try:
        bootstrap_database()
        print("Database schema is ready.")
    finally:
        close_all_connections()