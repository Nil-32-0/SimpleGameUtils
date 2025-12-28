import psycopg2
from config import load_config

def openConnection():
    """ Connect to the PostGreSQL Server """
    config = load_config()
    try:
        # connecting to the PostgreSQL server
        with psycopg2.connect(**config) as conn:
            # print('Connected to the PostgreSQL server.')
            return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

def queryData(query: str, *args: str, fetchAll = True):
    with openConnection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, args)

            if fetchAll:
                return cursor.fetchall()
            else:
                return cursor.fetchone()

def writeData(query: str, *args: str):
    result = None
    with openConnection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, args)
            if "returning" in query.lower():
                result = cursor.fetchall()
            connection.commit()
    if result is not None:
        return result