from backend.db import create_contracts_table, create_sla_table

if __name__ == "__main__":
    create_contracts_table()
    create_sla_table()
    print("Database initialized")