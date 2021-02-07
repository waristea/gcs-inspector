import logging, pp

def print_log(text, logging=True, pretty=False, type="info"): # verbosity unused
    if type=="info" and logging:
        if pretty:
            pp(text)
        else:
            print(text)
    elif type=="error":
        print(text)
