import argparse
from gcs_inspector.alerting import slack_post
from gcs_inspector.file_processor import write_file, safe_open_w, read_file, is_path_exist
from gcs_inspector.bucket_processor import create_client, list_buckets, get_buckets_info, get_message_v1, get_message_v2, get_message_v3, get_simplified_publics, check_diff
from gcs_inspector.custom_logging import print_log

def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(dest="service_account.json", help="Google service account json file path (eg: vocal-bridge-1111111.json)")
    parser.add_argument("-s", "--skip_object", default=False, action='store_true', help="skip checks for public objects")
    parser.add_argument("-x", "--silent", default=False, action='store_true', help="disable writing to screen (except errors)")
    parser.add_argument("-u", "--webhook_url", help="send results to this slack webhook url")
    parser.add_argument("-l", "--log", dest="log", default=False, action='store_true', help="enable output to the filename described")
    parser.add_argument("-f", "--filename", dest="filename", default="saved.json", help="change filename output")
    parser.add_argument("-o", "--out_folder", dest="folder", default="outputs", help="change folername output")
    parser.add_argument("-m", "--mode", default=0, type=int, choices=[0,1,2], help="0: Normal text; 1: Slack-formatted; 2: Only get difference from previous state (display mode 1)")

    return vars(parser.parse_args())

def gen_message(settings, buckets_info, project_name):
    IS_PRINT = not(settings["silent"])
    IS_SAVE_LOG = settings["log"]
    OUT_FOLDER = settings["folder"]
    SAVED_FILENAME = settings["filename"]
    MODE = settings["mode"]

    REL_FILE_PATH = OUT_FOLDER+"/"+SAVED_FILENAME

    message = ""
    if MODE==0:
        message = get_message_v1(buckets_info)
        if IS_SAVE_LOG:
            try:
                write_file(buckets_info, SAVED_FILENAME, rel_out_folder=OUT_FOLDER)
            except Exception as e:
                print_log(e, type="error")
                print_log("Failed to write file, make sure the path is correct", type="error")
    elif MODE==1:
        message = get_message_v2(buckets_info)
        if IS_SAVE_LOG:
            try:
                write_file(buckets_info, SAVED_FILENAME, rel_out_folder=OUT_FOLDER)
            except Exception as e:
                print_log(e, type="error")
                print_log("Failed to write file, make sure the path is correct", type="error")
    elif MODE==2:
        simplified_pub_bi = get_simplified_publics(buckets_info)
        if IS_SAVE_LOG:
            if is_path_exist(REL_FILE_PATH): # Checking if state file already exists
                try:
                    old_pub_bi = read_file(REL_FILE_PATH, type="json")
                    diffs = check_diff(old_pub_bi, simplified_pub_bi)
                    message = get_message_v3(diffs, project_name=project_name)
                except Exception as e:
                    print_log("Failed to read previous save file", type="error")

                try:# Replacing old state with new state
                    write_file(simplified_pub_bi, SAVED_FILENAME, rel_out_folder=OUT_FOLDER)
                except Exception as e:
                    print_log(e, type="error")
                    print_log("Failed to write file, make sure the path is correct", type="error")
            else:
                print_log("Initializing save file for comparison", LOGGING=IS_PRINT)
                message = get_message_v2(buckets_info)
                try:
                    write_file(simplified_pub_bi, SAVED_FILENAME, rel_out_folder=OUT_FOLDER)
                except Exception as e:
                    print_log(e, type="error")
                    print_log("Failed to write file. Make sure the path is correct", type="error")
    else:
        print_log("Mode Invalid, please input these options only: [0,1,2]", logging=IS_PRINT, type="error")

    return message

def main():
    settings = get_args()

    service_account_jsons = [settings["service_account.json"]]
    IS_CHECK_OBJECT_IAM = not(settings["skip_object"])
    IS_PRINT = not(settings["silent"])
    WEBHOOK_URL = settings["webhook_url"]
    IS_SAVE_LOG = settings["log"]

    for sa_json in service_account_jsons: # lists will be supported later
        try:
            client, project_name = create_client(sa_json)
        except Exception as e:
            print_log(e, type="error")
            print_log("Failed to create client. Are you sure you filled in the correct service account file path?", type="error")
            break

        buckets = list_buckets(client, project_name)
        buckets_info = get_buckets_info(buckets, check_object_iam=IS_CHECK_OBJECT_IAM, client=client, logging=IS_PRINT)

        message = gen_message(settings, buckets_info, project_name)
        print_log(message, pretty=False, logging=IS_PRINT)

        if WEBHOOK_URL:
            response = slack_post(WEBHOOK_URL, message)
            print_log(response.content, pretty=True, logging=IS_PRINT)

if __name__=="__main__":
    main()
