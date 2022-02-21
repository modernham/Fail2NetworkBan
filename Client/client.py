"""
Client script to send bans to the fail2BanNetwork server.
More than one host can be entered as a list.
EX: HOST_IP = ["192.168.1.4", "192.168.1.5"]
The Encryption string is really meant to OBSCURE information, and is not really secure.
Still yet, it will need to match the one on the server.
"""
import ipaddress, socket
import sys, os.path
import datetime

__author__ = "ModernHam"
__license__ = "GPLv3"
__credits__ = "gowhari"

HOST_IP = ["192.168.1.2"]
HOST_PORT = 1514
LOG = True
LOG_PATH = '/var/log/fail2networkban.log'
ENCRYPTION_STRING = "Password"

"""
https://gist.github.com/gowhari
Very basic vigenere cipher to encrypt the message being sent.
This is by no means secure, but it will make it much more difficult for someone within 
your internal network to understand the data and block your own IP's.
I did not want to add additional packages to the client, so this is what we will work with.
"""
def encrypt(string):
    encoded_chars = []
    for i in range(len(string)):
        key_c = ENCRYPTION_STRING[i % len(ENCRYPTION_STRING)]
        encoded_c = chr(ord(string[i]) + ord(key_c) % 256)
        encoded_chars.append(encoded_c)
    encoded_string = ''.join(encoded_chars)
    return encoded_string
"""
Checks if log file exists. If it doesn't create with new entry.
it does exist, we simply append the file with the newest entry.
"""
def log(name,action, ip):
    ct = str(datetime.datetime.now().now())
    if (os.path.exists(LOG_PATH)):
        with open(LOG_PATH , "a") as log:
            log.write("\n" + ct + " Name: " + str(name) + " Action : " + action + " IP: " + str(ip))
    else:
        with open(LOG_PATH, "w+") as log:
            log.write(ct + " Name: " + str(name) + " Action : " + action + " IP: " + str(ip))

#Used for input validation. Errors will be logged in the log file specified.
def loginfo(info):
    ct = str(datetime.datetime.now().now())
    if (os.path.exists(LOG_PATH)):
        with open(LOG_PATH , "a") as log:
            log.write("\n" + ct + " " + info)
    else:
        with open(LOG_PATH, "w+") as log:
            log.write(ct + " " + info)


"""
Send ban/unban information to the server.
We separate the data with a space for easy parsing on the server side.
"""
def sendinfo(name, action, ip):
    for host in HOST_IP:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host, HOST_PORT))
        except:
            if (LOG):
                loginfo("Could not establish connection to server, please check to make sure the IP is correct, and the port is open / not used")
            sys.exit(1)
        Data = encrypt(name + " " + action + " " + ip)
        client_socket.send(Data.encode())
        client_socket.close()


def validate_ip_address(address):
    try:
        ip = ipaddress.ip_address(address)
        return True
    except ValueError:
        return False


#Preform some input validation before we send data to the server.
if len(sys.argv) != 4:
    if (LOG):
        loginfo("Invalid argument count, please check your fail2ban action syntax")
    sys.exit(1)
if not validate_ip_address(sys.argv[3]):
    if (LOG):
        loginfo("Invalid Ip Address: " + sys.argv[3] + " , please check your fail2ban action syntax")
    sys.exit(1)
if sys.argv[2] != "ban" and sys.argv[2] != "unban":
    if (LOG):
        loginfo("Invalid action: " + sys.argv[2] + " , please check your fail2ban action syntax")
    sys.exit(1)
if (LOG):
    log(sys.argv[1],sys.argv[2], sys.argv[3])
sendinfo(sys.argv[1],sys.argv[2], sys.argv[3])
