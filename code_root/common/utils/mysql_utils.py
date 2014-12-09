"""Mysql query utilities."""
import MySQLdb


def get_mysql_connection(connector):
    """Get the connection object."""
    return MySQLdb.connect(host=connector['host'],
                           db=connector['db'],
                           user=connector['user'],
                           passwd=connector['passwd'])


def call_mysql(connector, query, do_write=False):
    """Executes a specific query on a specified mysql server.

    Returns:
        A tuple containing (exit_code(0 for success, non-zero for failure),
                            cursor rows, error text)
    """
    cursor = None
    connection_obj = None
    try:
        connection_obj = get_mysql_connection(connector)
        cursor = connection_obj.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        if do_write:
            cursor.close()
            cursor = None
            connection_obj.commit()
        errors = None
        return 0, results, errors
    except MySQLdb.Error as exp:
        errors = exp.args[1]
        return 1, None, errors
    finally:
        if do_write and cursor:
            cursor.close()
        if connection_obj:
            if do_write and errors is not None:
                connection_obj.rollback()
            connection_obj.close()
