import MySQLdb
import pprint
from dbConfig import host, user, password, db

pp = pprint.PrettyPrinter(indent=2)

class SQLDalConn(object):
  def __init__(self):
    try:
      self.conn = MySQLdb.connect(
        host=host,
        user=user,
        passwd=password,
        db=db
      )
    except Exception as err:
      print(f"""Issue connecting to database. Please ensure the host:database you are targeting 
        ({SQLDalConn.host}:{SQLDalConn.db}) exists and it has the user ({SQLDalConn.user}) assigned to it""")
      pp.pprint(err)
    self.x = self.conn.cursor()

  def executeMultipleInsertQueries(self, gameId, queries):
    try:
      for query in queries:
        self.x.execute(query)
    except Exception as err:
      self.conn.rollback()
      raise NameError(f'Error occured in executeMultipleInsertQueries: {err}')

      
  def executeInsertOrUpdateQuery(self, query):
    result = self.x.execute(query)
    self.conn.commit()
    print(f'Successfully updated {result} rows')


  def executeSelectQuery(self, query):
    self.x.execute(query)
    values = self.x.fetchall()

    print(f'Successfully executed query and retrieved {len(values)} results')

    return values

  def _closeConnection(self):
    self.conn.commit()
    self.x.close()
    self.conn.close()

