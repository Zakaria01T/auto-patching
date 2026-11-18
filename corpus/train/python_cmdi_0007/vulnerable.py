def download(url):
    import os
    os.system("curl -s -o page.html '%s'" % url)