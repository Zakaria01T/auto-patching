def get(self, email):
    """ Fetch data for admin with the corresponding email """
    return database_utilities.execute_query("""select * from admins where email = %s""", (email, ))