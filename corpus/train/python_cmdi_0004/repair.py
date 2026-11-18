def resolve(domain):
    import socket
    return socket.gethostbyname_ex(domain)