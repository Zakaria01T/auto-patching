def backup_database(dbname, dump_path):
    import subprocess
    with open(dump_path, "wb") as output:
        subprocess.run(["pg_dump", "--", dbname], stdout=output, check=True)
