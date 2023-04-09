import requests

payload = {}
files = {}
headers = {}


def httpGet(ip):
    response = requests.request("GET", ip, headers=headers, data=payload, files=files)


def turnOffTheFocusDistance(ip):
    url = ip + "/settings/focus_distance?set=off"
    response = requests.request("GET", url, headers=headers, data=payload, files=files)


def setTheFocusDistance(ip, focus_value):
    url = ip + "/settings/focus_distance?set=" + str(focus_value)
    response = requests.request("GET", url, headers=headers, data=payload, files=files)
