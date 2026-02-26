import psycopg2

conn=psycopg2.connect(
    host='localhost',
    port=5432,
    user='postgres',
    password='rty67jouj',
    database='construction_db'
)

cur = conn.cursor()

def get_data(table):
    cur.execute(f"select * from{table}")
    data= cur.fetchall()
    return data


def get_clients():
    cur.execute(
        "select * from clients"
    )
    clients= cur.fetchall()
    return clients


clients=get_clients()
print(clients)

def insert_clients(values):
    cur.execute(f"insert into clients(name,phone,email, address)values{values}")

    conn.commit()

client1= ('Mary lana','0706345612', 'mary@gmail.com','Kisii')
insert_clients(client1)

def get_employees():
    cur.execute("select* from employees")
    employees=cur.fetchall()
    return employees

employees=get_employees()


def insert_employees(values):
    cur.execute(f"insert into employees (full_name,role,phone,salary) values{values}")

    conn.commit()

employee1=('joe otieno','mason','0722334455','45000')
insert_employees(employee1)
print(employees)

def get_projects():
    cur.execute("select * from projects")
    projects=cur.fetchall()
    return projects

projects=get_projects()

def insert_project(values):
    cur.execute(f"insert into projects (project_name,location,budget) values{values}")

    conn.commit()

project1=('nairobi_home','nairobi','10000000')
insert_project(project1)
print(projects)




def get_materials():
    cur.execute("select * from materials")
    materials=cur.fetchall()
    return materials
materials=get_materials()


def insert_materials(values):
    cur.execute(f"insert into materials (material_name,unit,unit_price,stock_quantity) values{values}")

    conn.commit()

material1=('cement','bags',1500,100)
insert_materials(material1)
print(materials)





