import psycopg2
from config import config
import os 

def load_records_from_db():
    """ Connect to the database server """
    conn = None

    # read connection parameters
    params = config()

    # connect to the PostgreSQL server
    print('Connecting to the database...')
    conn = psycopg2.connect(**params)
    
    # create a cursor
    cur = conn.cursor()
    
    # execute a statement
    print('PostgreSQL database version:')
    cur.execute('SELECT version()')

    # display the PostgreSQL database server version
    db_version = cur.fetchone()
    print(db_version)
    
    postgreSQL_select_Query = f"select {os.getenv('TABLE_QUERY')} from {os.getenv('QUERIED_TABLE')}"
        
    cur.execute(postgreSQL_select_Query)
    print("Selecting rows from table using cursor.fetchall")
    
    mobile_records = cur.fetchall()

    # close the communication with the PostgreSQL
    cur.close()
    
    return mobile_records