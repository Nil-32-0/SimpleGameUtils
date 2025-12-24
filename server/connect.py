import psycopg2
from config import load_config

def openConnection():
    """ Connect to the PostGreSQL Server """
    config = load_config()
    try:
        # connecting to the PostgreSQL server
        with psycopg2.connect(**config) as conn:
            print('Connected to the PostgreSQL server.')
            return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

def writeData(query: str, *args: str):
    with openConnection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, args)
            result = cursor.fetchall()
            connection.commit()
    return result