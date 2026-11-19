def backup_database(dbname, dump_path):
    import os
    cmd = "pg_dump " + dbname + " > " + dump_path
    os.system(cmd)
