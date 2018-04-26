from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
# Create a class that will give us an object that we can use to connect to a database
class MySQLConnection(object):
    def __init__(self, app, db):
        config = {
                'host': 'host',
                'database': db, # we got db as an argument
                'user': 'root',
                'password': 'root',
                'port': '3306' # change the port to match the port your SQL server is running on
        }
        DATABASE_URI = "mysql://{}:{}@127.0.0.1:{}/{}".format(config['user'], config['password'], config['port'], config['database'])   # this will use the above values to generate the path to connect to your sql database
        app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
        self.db = SQLAlchemy(app)  # establish the connection to database

    def query_db(self, query, data=None):              # this is the method we will use to query the database
        result = self.db.session.execute(text(query), data)
        if query[0:6].lower() == 'select':             # if the query was a select
            list_result = [dict(r) for r in result]    # convert the result to a list of dictionaries
            return list_result                         # return the results as a list of dictionaries
        elif query[0:6].lower() == 'insert':           # if the query was an insert, return the id of the
            self.db.session.commit()                   # commit changes
            return result.lastrowid                    # row that was inserted
        else:
            self.db.session.commit()                   # if the query was an update or delete, return nothing and commit changes

def MySQLConnector(app, db):                           # This is the module method to be called by the user in server.py. Make sure to provide the db name!
    return MySQLConnection(app, db)
