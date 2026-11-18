def resolve(domain):
    import os
    return os.popen("nslookup " + domain).read()