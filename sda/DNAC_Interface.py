import requests
import urllib3
from requests.auth import HTTPBasicAuth
import json

urllib3.disable_warnings()

def aaa():
    print "***** Authenticating to DNAC  *****"
    username = ''
    password = ''
    url = 'https://lm-dnac.labminutes.com/api/system/v1/auth/login'

    resp = requests.get(url, auth=HTTPBasicAuth(username, password), verify=False)

    if resp.status_code == 200:
        print 'Connection Successful'
        return {'Cookie': resp.headers['set-cookie']}
    else:
        print 'Connection Failed'
        exit(1)

def getDeviceID(deviceName, headers):
    print "***** Getting Device ID " + deviceName + " *****"
    url = "https://lm-dnac.labminutes.com/api/v1/network-device?hostname=" + deviceName

    resp = requests.get(url, headers=headers, verify=False)

    if resp.status_code == 200:
        respJson = resp.json()
        return respJson['response'][0]['id']
    else:
        print 'Failed to get Device ID'
        exit(1)

def getIntID(intName, deviceID, headers):
    print "***** Getting Interface ID " + intName + " *****"
    url = "https://lm-dnac.labminutes.com/api/v1/interface/network-device/" + deviceID

    resp = requests.get(url, headers=headers, verify=False)

    if resp.status_code == 200:
        respJson = resp.json()
        # Look for desired interface
        for int in respJson['response']:
            if int['portName'] == intName:
                return int['id']
        else:
            print 'Cannot find specificed interface ' + intName
            exit(1)
    else:
        print 'Failed to get Interface ID'
        exit(1)

def getSegmentID(vnName, headers):
    print "***** Getting Segment ID " + vnName + " *****"
    url = "https://lm-dnac.labminutes.com/api/v2/data/customer-facing-service/Segment?name=" + vnName

    resp = requests.get(url, headers=headers, verify=False)

    if resp.status_code == 200:
        respJson = resp.json()
        return respJson['response'][0]['id']
    else:
        print 'Failed to get Segment ID'
        exit(1)

def getAuthProfileID(authProfile, headers):
    print "***** Getting AuthProfile ID " + authProfile + " *****"
    url = "https://lm-dnac.labminutes.com/api/v1/siteprofile?name=" + authProfile

    resp = requests.get(url, headers=headers, verify=False)

    if resp.status_code == 200:
        respJson = resp.json()
        return respJson['response'][0]['siteProfileUuid']
    else:
        print 'Failed to get AuthProfile ID'
        exit(1)

def getDeviceConfig(deviceName, deviceID, headers):
    print "***** Getting Device Config " + deviceName + " *****"
    url = "https://lm-dnac.labminutes.com/api/v2/data/customer-facing-service/DeviceInfo?networkDeviceId=" + deviceID

    resp = requests.get(url, headers=headers, verify=False)

    if resp.status_code == 200:
        respJson = resp.json()
        return respJson['response'][0]
    else:
        print 'Failed to get Device Config'
        exit(1)

def putDeviceConfig(deviceName, deviceConfig, headers):
    print "***** Putting Device Config " + deviceName + " *****"
    url = "https://lm-dnac.labminutes.com/api/v2/data/customer-facing-service/DeviceInfo"
    deviceConfig = '[' + json.dumps(deviceConfig) + ']'
    print deviceConfig
    #exit(0)
    resp = requests.put(url, data=deviceConfig, headers=headers, verify=False)
    respJson = resp.json()

    if resp.status_code == 202:
        return respJson['response']['taskId']
    else:
        print resp.reason
        print respJson['response']['message']
        print 'Failed to put Device Config'
        exit(1)

def getTaskInfo(taskID, headers):
    print "***** Getting Task Info *****"
    url = "https://lm-dnac.labminutes.com/api/v1/task/" + taskID

    resp = requests.get(url, headers=headers, verify=False)

    if resp.status_code == 200:
        respJson = resp.json()
        if respJson['response']['isError'] == 'true':
            print 'Task Failed due to ' + respJson['response']['failureReason']
        else:
            print 'Task Succeeded'
        return
    else:
        print 'Failed to get Task Info Config'
        exit(1)

def buildIntConfig(deviceID, intName, dataVN, voiceVN, authProfile, headers):


    # Get Interface ID
    intID = getIntID(intName, deviceID, headers)

    # Get Data Segment ID
    dataSegmentID = getSegmentID(dataVN, headers)

    # Get Voice Segment ID
    voiceSegmentID = getSegmentID(voiceVN, headers)

    # Get AuthProfile ID
    authProfileID = getAuthProfileID(authProfile, headers)

    # Create Interface Config
    intConfig = {
        "interfaceId": intID,
        "authenticationProfileId": authProfileID,
        "connectedToSubtendedNode": False,
        "role": "LAN",
        "segment": [
            {'idRef': dataSegmentID},
            {'idRef': voiceSegmentID}
        ]
    }
    return intConfig


#**************** Main ********************
deviceName = "LM-E2.labminutes.com"
intName = ["1/0/16", "1/0/17", "1/0/18"]
dataVN = "172_16_66_0-GUEST"
voiceVN = "172_16_67_0-PROD"
authProfile = "Closed Authentication"

# Get DNAC Session Cookie
headers = aaa()
headers['content-type'] = 'application/json'

# Get Device ID
deviceID = getDeviceID(deviceName, headers)

# Get Device Config
deviceConfig = getDeviceConfig(deviceName, deviceID, headers)

intConfig = []
for int in intName:
    temp = buildIntConfig(deviceID, 'GigabitEthernet' + int, dataVN, voiceVN, authProfile, headers)
    # Add to device Config
    deviceConfig['deviceInterfaceInfo'].append(temp)

# Send config to DNAC
taskID = putDeviceConfig(deviceName, deviceConfig, headers)

# Get task Info
taskInfo = getTaskInfo(taskID, headers)

