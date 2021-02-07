import requests, json

def slack_post(full_webhook_url=None, content="", base_url=None, workspace_id=None, channel_id=None, webhook_id=None):
    if not(full_webhook_url):
        if base_url and workspace_id and channel_id and webhook_id:
            full_webhook_url = "/".join([base_url,workspace_id,channel_id,webhook_id])
        else:
            print("Please input webhook URL")
            return
    char_limit = 100000 #char limit of slack api

    for i in range(0,len(content),char_limit):
        headers = {'Content-type': 'application/json'}
        payload = {"text":content[i:i+char_limit]}
        response = requests.post(full_webhook_url, data=json.dumps(payload), headers=headers)
        return response
