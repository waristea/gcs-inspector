import pp, requests
import os, os.path, pathlib, errno, json
from gcs_inspector.custom_logging import print_log

# File Read/Write
def is_path_exist(filepath):
    return os.path.isfile(filepath)

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def safe_open_w(path):
    # Open "path" for writing, creating any parent directories as needed.
    mkdir_p(os.path.dirname(path))
    return open(path, "w")


def write_file(content, filename, type="json", rel_out_folder="outputs"):
    out_folder = str(pathlib.Path(__file__).parent.absolute())+"/"+rel_out_folder+"/"
    file_path = out_folder+filename

    try:
        with safe_open_w(file_path) as f:
            if type=="json":
                json.dump(content, f, ensure_ascii=False, indent=4)
            else:
                print_log("File format is not valid", type="error")
                return
    except Exception as e:
        print_log("An error has occured when writing the output file", type="error")
        print_log(e, type="error")
        return


def read_file(filename, type="raw", is_root=False):
    file_path = "/"
    if not(is_root):
        file_path = str(pathlib.Path(__file__).parent.absolute())+"/"+filename
    try:
        with open(file_path, "r") as f:
            data = f.read()
        if type=="json":
            return json.loads(data)
        elif type=="raw":
            return data
        else:
            print_log("File format is not valid", type="error")
            return
    except Exception as e:
        print_log("An error has occured when opening the file: "+filename, type="error")
        print_log(e, type="error")
        return

def get_latest_json_filename(foldername, format="-all_scopes.json", last=0):
    path = str(pathlib.Path(__file__).parent.absolute())+"/"+foldername+"/"

    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            if format in file:
                files.append(file)
    return sorted(files)[-last:]

def remove_oldest_jsons(foldername, format="-all_scopes.json", spared_amount=3):
    filenames = get_latest_json_filename(foldername, format)
    out_folder = str(pathlib.Path(__file__).parent.absolute())+"/"+foldername+"/"
    for i in range(len(filenames)-spared_amount):
        path = out_folder+filenames[i]
        os.remove(path)

def get_latest_jsons(foldername, format="-all_scopes.json", last=2):
    json_all_name = get_latest_json_filename(foldername, format, last)
    json_all = []
    for name in json_all_name:
        json_all.append(read_file(foldername+"/"+name, "json"))
    return json_all
