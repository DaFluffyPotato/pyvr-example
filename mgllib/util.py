def read_f(path):
    f = open(path, 'r')
    data = f.read()
    f.close()
    return data