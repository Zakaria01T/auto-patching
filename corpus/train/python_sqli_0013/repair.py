@jwt_required
def delete(self, email):
    """ Deletes admin with the corresponding email """
    return database_utilities.execute_query("""delete from admins where email = %s""", (email, ))