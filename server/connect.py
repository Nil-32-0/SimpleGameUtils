import psycopg2
from config import load_config

def connect():
    """ Connect to the PostGreSQL Server """
    config = load_config()
    try:
        # connecting to the PostgreSQL server
        with psycopg2.connect(**config) as conn:
            print('Connected to the PostgreSQL server.')
            return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

if __name__ == '__main__':
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT useruuid FROM users")
    print(cur.fetchall())

    cur.execute("INSERT INTO users(useruuid, username) VALUES(%s, %s) RETURNING useruuid;", ("blegh", "null"))
    conn.commit()

    cur.execute("SELECT useruuid FROM users")
    print(cur.fetchall())