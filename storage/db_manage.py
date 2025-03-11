import sys
from db import engine
from models import onlineOrderReport, storeSalesReport

def create_tables():
    
    onlineOrderReport.metadata.create_all(engine)
    storeSalesReport.metadata.create_all(engine)

def drop_tables():
    
    onlineOrderReport.metadata.drop_all(engine)
    storeSalesReport.metadata.drop_all(engine)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        drop_tables()
        print("All tables droped!")
    create_tables()
    print("Empty tables created!")