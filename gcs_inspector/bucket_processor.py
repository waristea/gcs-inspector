import google.auth
from google.oauth2 import service_account
from google.cloud import storage
from gcs_inspector.file_processor import print_log

def create_client(service_account_json=None):
    project = None
    if service_account_json:
        cred = service_account.Credentials.from_service_account_file(service_account_json)
        project = cred._project_id
    else:
        cred, project = google.auth.default()

    client = storage.Client(credentials=cred, project=project)

    return client, project

def list_buckets(client, project=None, name_only=False):
    if name_only:
        return [b.name for b in client.list_buckets()]
    return [b for b in client.list_buckets()]

def get_iam_policy_wrapped(bucket, client): # need 2 do this because it returns a set. which is undumpable to json
    policies = bucket.get_iam_policy(client)
    new_policies = {}
    for k,v in policies.items():
        new_policies[k] = list(v)
    return new_policies

def get_buckets_info(buckets, check_object_iam=False, client=None, logging=False):
    bucket_info = {}
    for b in buckets:
        policy = get_iam_policy_wrapped(b, client)
        blobs_dict = {}
        uniform_access = b.iam_configuration.uniform_bucket_level_access_enabled
        if not(uniform_access) and check_object_iam:
            blobs = b.list_blobs()
            for blob in blobs:
                try:
                    blob_policy = get_iam_policy_wrapped(b, client)
                except Exception as e:
                    print_log("Error occurred", logging=logging)
                    print_log(e, logging=logging)
                    break
                else:
                    #print(b.name+" "+blob.name+" "+blob.public_url+" "+blob.self_link)
                    blob_public_policy = get_public_members(blob_policy)
                    blobs_dict[blob.name] = {"policy":blob_policy,"public_members":blob_public_policy, "self_link":blob.self_link}
        public_policy = get_public_members(policy)
        url = b.self_link
        bucket_info[b.name] = {"policy":policy, "public_members":public_policy, "url":url, "blobs":blobs_dict, "uniform-access":uniform_access}
    return bucket_info

def get_public_members(policy):
    PUBLIC_USERS = {"allUsers", "allAuthenticatedUsers"}
    ROLES = ["roles/iam.securityAdmin", "roles/iam.securityReviewer", "roles/storage.admin", "roles/storage.legacyBucketOwner", "roles/storage.legacyBucketReader", "roles/storage.legacyBucketWriter", "roles/storage.legacyObjectOwner", "roles/storage.legacyObjectReader", "roles/storage.objectAdmin", "roles/storage.objectCreator", "roles/storage.objectViewer"]

    public_policy = {}
    for role, members in policy.items():
        public_members = set(members).intersection(PUBLIC_USERS)
        if public_members:
            for member in public_members:
                if member in public_policy:
                    public_policy[member].append(role)
                else:
                    public_policy[member] = [role]

    if public_policy:
        return public_policy
    return None

def get_public_permission_message(public_members_policy, is_blob=False):
    message = "Public Permissions : "

    if is_blob:
        message = "Blob " + message

    if len(public_members_policy)==0:
        message += "None"
    else:
        message += "\n"
        for member, role in public_members_policy.items():
            message += "- {} {} \n".format(member, role)
    return message

def get_public_permission_message_v2(public_members_policy, is_blob=False):
    message = "Allowed: "
    if len(public_members_policy)==0:
        message += "None"
    else:
        member_list = []
        for member, role in public_members_policy.items():
            member_n_role = str(member) + " " + str(role)
            member_list.append(member_n_role)
        message += str(member_list)
    return message

def get_simplified_publics(buckets_info): #v2 # save this to get changes over time
    simplified_bi = {} # {bucket_name:{"public_members":{"member":member, "role":role}, "blobs":{blob_name:{"link":link,"public_members":{"member":member, "role":role}}}}}
    for bucket_name, bucket_prop in buckets_info.items():
        blobs = bucket_prop["blobs"]

        if ("public_members" in bucket_prop) and bucket_prop["public_members"]: # if bucket is public, all is public
            simplified_bi[bucket_name]={"public_members":bucket_prop["public_members"], "blobs":blobs}

        for blob_name, blob_prop in blobs.items():
            if ("public_members" in blob_prop) and blob_prop["public_members"]: # if bucket is not public, but blob is set using ACL to be public
                if bucket_name not in simplified_bi.keys():
                    simplified_bi[bucket_name]={"public_members":bucket_prop["public_members"], "blobs":{}}
                blob_filtered = { "link": blob_prop["self_link"], "public_members": blob_prop["public_members"]}
                simplified_bi[bucket_name]["blobs"][blob_name] = blob_filtered
    return simplified_bi

def get_message_v1(buckets_info, check_object_iam=False, project_name=""):
    PUBLIC_HEADER = "Public Buckets of Project "
    EQUALS_DELIM = "="*30+"\n"
    STRIPE_DELIM = "-"*30+"\n"

    ERROR_MSG = "Bucket info parse error. Check script for exceptions"

    if not(buckets_info):
        return ERROR_MSG

    buckets_message = ""
    for bucket_name, bucket_prop in buckets_info.items():
        if ("public_members" in bucket_prop) and bucket_prop["public_members"]:
            buckets_message += EQUALS_DELIM
            buckets_message += bucket_name+"\n"
            buckets_message += get_public_permission_message(bucket_prop["public_members"])

        blobs = bucket_prop["blobs"]
        for blob_name, blob_prop in blobs.items():
            if ("public_members" in blob_prop) and blob_prop["public_members"]:
                buckets_message += STRIPE_DELIM
                buckets_message += "Bucket : "+bucket_name+"\n"
                buckets_message += "Blob   : "+blob_name+"\n"
                buckets_message += "Link   : "+blob_prop["self_link"]+"\n"
                buckets_message += get_public_permission_message(blob_prop["public_members"], True)

    if project_name==None:
        project_name = ""

    message = PUBLIC_HEADER + project_name + ":\n" + STRIPE_DELIM + buckets_message + EQUALS_DELIM
    if len(buckets_message)==0:
        message += "No public buckets or blobs are available\n"

    if check_object_iam:
        message += STRIPE_DELIM
        message += "Blob/Object level IAM is checked"

    return message

def get_message_v2(buckets_info, check_object_iam=False, project_name=""):
    PUBLIC_HEADER = "Public Buckets of Project "
    EQUALS_DELIM = "="*30+"\n"
    STRIPE_DELIM = "-"*30+"\n"

    ERROR_MSG = "Bucket info parse error. Check script for exceptions"

    if not(buckets_info):
        return ERROR_MSG

    message = ""
    buckets_message = ""
    for bucket_name, bucket_prop in buckets_info.items():
        buckets_message += EQUALS_DELIM
        buckets_message += "Bucket : "+bucket_name+"\n"
        if ("public_members" in bucket_prop) and bucket_prop["public_members"]:
            buckets_message += get_public_permission_message_v2(bucket_prop["public_members"])

        blobs = bucket_prop["blobs"]
        for blob_name, blob_prop in blobs.items():
            if ("public_members" in blob_prop) and blob_prop["public_members"]:
                pub_permission_msg = get_public_permission_message_v2(blob_prop["public_members"], True)
                buckets_message += "- <"+blob_prop["self_link"]+"|"+blob_name+">"
                buckets_message += "({})\n".format(pub_permission_msg)

    if project_name==None:
        project_name = ""

    message = PUBLIC_HEADER + project_name + ":\n" + STRIPE_DELIM + buckets_message + EQUALS_DELIM
    if len(buckets_message)==0:
        message += "No public buckets or blobs are available\n"

    if check_object_iam:
        message += STRIPE_DELIM
        message += "Blob/Object level IAM is checked"

    return message

def check_dict_key_diff(dict_before, dict_after):
    before_dict_key_set = set(dict_before.keys())
    after_dict_keys_set = set(dict_after.keys())

    deleted_dict_keys = before_dict_key_set-after_dict_keys_set
    added_dict_keys = after_dict_keys_set-before_dict_key_set
    intersecting_dict_keys = after_dict_keys_set.intersection(before_dict_key_set)

    return (list(deleted_dict_keys), list(added_dict_keys), list(intersecting_dict_keys))

def check_diff(bucket_info_simp_before, bucket_info_simp_after):
    key_history_before = []

    bucket_diff = check_dict_key_diff(bucket_info_simp_before, bucket_info_simp_after)

    intersecting_bucket_keys = bucket_diff[2]

    if len(bucket_diff[0])>0:
        deleted_keys_list = [bucket_diff[0]]
    else:
        deleted_keys_list = []

    if len(bucket_diff[1])>0:
        added_keys_list = [bucket_diff[1]]
    else:
        added_keys_list = []

    changed_blob_properties = {}

    after_metadata = {"bucket_count": len(bucket_info_simp_after)}

    if bucket_info_simp_before==bucket_info_simp_after:
        after_metadata = {"bucket_count": len(bucket_info_simp_after)}
        return (deleted_keys_list, added_keys_list, changed_blob_properties, after_metadata)

    for k1 in intersecting_bucket_keys:
        before_blob = bucket_info_simp_before[k1]["blobs"]
        after_blob = bucket_info_simp_after[k1]["blobs"]

        if before_blob==after_blob:
            continue

        blob_diff = check_dict_key_diff(before_blob, after_blob)

        deleted_blob_keys = blob_diff[0]
        added_blob_keys = blob_diff[1]
        intersecting_blob_keys = blob_diff[2]

        if len(deleted_blob_keys)!=0:
            deleted_keys_list.append([k1, "blob", deleted_blob_keys])
        if len(added_blob_keys)!=0:
            added_keys_list.append([k1, "blob", added_blob_keys])

        for k2 in intersecting_blob_keys:
            if (before_blob[k2]["link"]!=after_blob[k2]["link"]):
                changes = {"before":before_blob[k2]["link"], "after":after_blob[k2]["link"]}
                changed_blob_properties[[k1, "blob", k2, "link"]] = changes
            if (before_blob[k2]["public_members"]!=after_blob[k2]["public_members"]):
                changes = {"before":before_blob[k2]["public_members"], "after":after_blob[k2]["public_members"]}
                changed_blob_properties[[k1, "blob", k2, "public_members"]] =  changes

    return (deleted_keys_list, added_keys_list, changed_blob_properties, after_metadata)

def get_message_v3(diffs, project_name=""):
    PUBLIC_HEADER = "Changes in "
    EQUALS_DELIM = "="*30+"\n"

    ERROR_MSG = "Bucket info parse error. Check script for exceptions"

    if not(buckets_info):
        return ERROR_MSG

    message = ""
    buckets_message = ""
    if len(diffs[0])==0 and len(diffs[1])==0 and len(diffs[2])==0:
        message += "No changes detected \n"
    else:
        if len(diffs[0])>0:
            buckets_message += EQUALS_DELIM
            for d in diffs[0]:
                if len(d)==1:
                    buckets_message += "Public bucket deleted: "+str(d)+"\n"
                else:
                    for blob in d[2]:
                        buckets_message += "Public blob deleted: "+blob+"\n"
        if len(diffs[1])>0:
            buckets_message += EQUALS_DELIM
            for d in diffs[1]:
                if len(d)==1:
                    buckets_message += "Public bucket added: "+str(d)+"\n"
                else:
                    for blob in d[2]:
                        buckets_message += "Public blob added: "+blob+"\n"

        if len(diffs[2])>0:
            for k, v in diffs[2].items():
                buckets_message += EQUALS_DELIM
                buckets_message += "Property `{}` of {}/{} changed:\n".format(k[3],k[0],k[2])
                buckets_message += "Before : `{}`\n".format(v["before"])
                buckets_message += "After  : `{}`\n".format(v["after"])

        if project_name==None:
            project_name = ""

        message = PUBLIC_HEADER + project_name + ":\n" + buckets_message + EQUALS_DELIM

    return message
