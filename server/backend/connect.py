import psycopg2
from config import load_config

def openConnection(filename='database.ini'):
    """ Connect to the PostGreSQL Server """
    config = load_config(filename)
    try:
        # connecting to the PostgreSQL server
        return psycopg2.connect(**config)
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

def queryData(connection, query: str, *args: str, fetchAll = True):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(query, args)

            if fetchAll:
                return cursor.fetchall()
            else:
                return cursor.fetchone()

def writeData(connection, query: str, *args: str):
    result = None
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(query, args)
            if "returning" in query.lower():
                result = cursor.fetchall()
        connection.commit() # Auto called at end of with block, but nice to call explicitly
    if result is not None:
        return result