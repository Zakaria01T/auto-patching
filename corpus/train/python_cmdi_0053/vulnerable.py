def inspect_document_path(path):
    import os
    return os.popen("file " + path).read()