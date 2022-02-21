"""
Python server to listen to fail2ban clients.
Server IP of 0.0.0.0 will listen on all interfaces
The Encryption string is really to OBSCURE information, and is not really secure.
Still yet, the password needs to match the one on the client.
"""
import socket, ipaddress
import datetime
import os, sys
import atexit

__author__ = "ModernHam"
__license__ = "GPLv3"
__credits__ = "gowhari"

SERVER_IP = "0.0.0.0"
SERVER_PORT = 1514
LOG = True
LOG_PATH = '/var/log/fail2networkban.log'
ENCRYPTION_STRING = "Password"
CLUSTER_FW_PATH = "/etc/pve/firewall/cluster.fw"
WHITELIST = ["192.168.1.1"]

"""
https://gist.github.com/gowhari
Very basic vigenere cipher to encrypt the message being sent.
This is by no means secure, but it will make it much more difficult for someone within 
your internal network to understand the data and block your own IP's.
I did not want to add additional packages to the client, so this is what we will work with.
"""
def decrypt(string):
    encoded_chars = []
    for i in range(len(string)):
        key_c = ENCRYPTION_STRING[i % len(ENCRYPTION_STRING)]
        encoded_c = chr((ord(string[i]) - ord(key_c) + 256) % 256)
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

def loginfo(info):
    ct = str(datetime.datetime.now().now())
    if (os.path.exists(LOG_PATH)):
        with open(LOG_PATH , "a") as log:
            log.write("\n" + ct + " " + info)
    else:
        with open(LOG_PATH, "w+") as log:
            log.write(ct + " " + info)

"""
Checks for the [IPSET blacklist] header, and adds it if it doesn't exist.
IP's are added just below the header. This is probably more memory intensive than it needs to be
but there are not many options with the standard library 
"""
def AddIP(data):
    IP_INSERT = data.split()[2] + "\n"
    #Checking for IPSET blacklist header, adding if it doesn't exist.
    try:
        with open(CLUSTER_FW_PATH, 'r+') as firewall:
            Lines = firewall.readlines()
            if "[IPSET blacklist]\n" not in Lines:
                firewall.write("\n\n[IPSET blacklist]\n")
        with open(CLUSTER_FW_PATH, 'r+') as firewall:
            contents = firewall.readlines()
            if "[IPSET blacklist]" in contents[-1]:  # Handle last line to prevent IndexError
                contents.append(IP_INSERT)
            else:
                for index, line in enumerate(contents):
                    if "[IPSET blacklist]" in line and IP_INSERT not in contents[index + 1]:
                        contents.insert(index + 1, IP_INSERT)
                        break
            firewall.seek(0)
            firewall.writelines(contents)
            if (LOG):
                loginfo("Created Block Entry for IP: " + data.split()[2] + " Application: " + data.split()[0])
    except:
        if LOG:
            loginfo("Unable to open " + CLUSTER_FW_PATH)

    return

"""
Once again, more memory intensive than needed.
If anyone has a more efficient way of doing this with the standard library, I'd love to know.
"""
def RemoveIP(data):
    try:
        with open(CLUSTER_FW_PATH, "r+") as f:
            d = f.readlines()
            f.seek(0)
            for i in d:
                if i != data.split()[2] + "\n":
                    f.write(i)
            f.truncate()
        loginfo("Removed Entry for IP: " + data.split()[2] + " Application: " + data.split()[0])
    except:
        if LOG:
            loginfo("Unable to open " + CLUSTER_FW_PATH)
    return

def validate_ip_address(address):
    try:
        ip = ipaddress.ip_address(address)
        return True
    except ValueError:
        return False

"""
Listens for data for the designated port. 
If it's received, it will decrypt it and preform basic input validation before blocking on the host.
"""
def receive_data():
    server_socket = socket.socket()
    try:
        server_socket.bind((SERVER_IP, SERVER_PORT))
    except:
        if (LOG):
            loginfo("Unable to bind to socket: " + SERVER_IP +  str(SERVER_PORT))
        sys.exit(1)
    server_socket.listen(1)

    #Continous Loop to listen for Fail2NetworkBan Clients.
    while True:
        conn, address = server_socket.accept()
        if (LOG):
            loginfo("Connection from: " + str(address))
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            data = decrypt(data)
            #Preform input validation
            if len(data.split()) != 3:
                if LOG:
                    loginfo("Invalid number of arguments: " + data)
                break
            if not validate_ip_address(data.split()[2]):
                if LOG:
                    loginfo("Invalid Ip Address" + str(data.split()))
                break
            if data.split()[2] in WHITELIST:
                if LOG:
                    loginfo("Ip Address: " + data.split()[2] + " is in the whitelist, ignoring")
                break
            if data.split()[1] == "ban":
                AddIP(data)
            elif data.split()[1] == "unban":
                RemoveIP(data)
            else:
                if LOG:
                    loginfo("Invalid Action:" + data.split()[1])
        conn.close()

def exit_handler():
    if LOG:
        loginfo("Application Terminated")

if __name__ == '__main__':
    if LOG:
        loginfo("Started service on port: " + str(SERVER_PORT))
    atexit.register(exit_handler)
    receive_data()


