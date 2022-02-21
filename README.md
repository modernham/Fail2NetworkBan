# Fail2NetworkBan

Fail2NetworkBan is a simple python client/server to direct bans from fail2ban to another host. At the moment Proxmox is the only host supported. Bans sent to the host will be banned for the whole hypervisor, and all VMs running inside it. More than one host is supported.

## What problems does this tool address?
1. If you are running a reverse proxy, sometimes it can be difficult to ban a specific host, even when you have the ip address.
2. Bad actors should really be banned network wide, this tool will accomplish that.
## Security concerns
I didn't want to use any third party modules, and wanted to keep things as simple as possible. Because of this, network traffic is encoded with a vigenere cipher. It won't stop a determined hacker who has internal access to your network, but it will at least provide some layer of obfuscation. Given that, if a hacker is in your network, and reverse engineers the obfuscation, and you haven't whitelisted your IP per instructions below, its possible to be blocked from your own hypervisor.
## Prerequisites
1. You must enable the top level firewall for your Proxmox hypervisor
This can typically be done by navigating to:  Datacenter -> Firewall -> Options -> Firewall Checked 

Also note, you must have a port open for communication with the client if the firewall is not  set to "Accept" , By default this is port 1514

2. You must have a working fail2ban install that obtains valid IPs already. Refer to this link if you need help with this: 
https://www.plesk.com/blog/various/using-fail2ban-to-secure-your-server/
3. You must have python3 on both client and server. This usually comes by default with fail2ban/proxmox, but you can install it with "sudo apt-get install python3"
## Installation Client (Debian/Ubuntu Based Distros):

The client is the object that sends failure data to the server. 
The server/hypervisor will be the object that actually blocks the IP.
First we will download the client python file called from fail2ban.
```bash
sudo apt-get install wget
mkdir fail2networkban
cd fail2networkban
wget https://github.com/modernham/Fail2NetworkBan/raw/main/Client/client.py
```
Open the downloaded "client.py" with an editor such as nano and modify the host ip, port, and password to your liking. You can add more than one host as anotated in the comments. Please note your password as you will need the same one on the server.

Now we will add our custom fail2ban action resposible for calling the python script above.
``` 
sudo nano /etc/fail2ban/action.d/fail2networkban.conf
```
Paste in the following content, modify the file path for both the "actionban" and "actionunban" to point to the client.py file we downloaded above. Example : /home/users/yourusername/fail2networkban/client.py
```bash
[Definition]

actionstart = touch /var/run/fail2ban/fail2ban.fail2networkban

actionstop = rm -f /var/run/fail2ban/fail2ban.fail2networkban

actioncheck = 

actionban = python3 /path/to/client.py <name> "ban" <ip>

actionunban = python3 /path/to/client.py <name> "unban" <ip>

[Init]

init = ServiceNameHere Notifications
```
Next we need to moify our jail to point to your custom action so that it sends data to the host.
Open the jail set up for your service. These are typically stored in /etc/fail2ban/jail.d

Change the action to our custom action. An example with my jellyfin install is:
```
[jellyfin]
findtime  = 3600
maxretry = 3
port   = 80,443
enabled = true
action = fail2networkban[name=jellyfin, bantime=600]
logpath = /var/log/jellyfin/*.log
```
Next we will restart Fail2Ban and verify its status.
```
sudo service fail2ban restart
sudo service fail2ban status
```


## Installation Server (Proxmox):
```bash
mkdir fail2networkban
cd fail2networkban
wget https://github.com/modernham/Fail2NetworkBan/raw/main/Server/Proxmox/server.py
```
Open the "server.py" with your favorite editor, and modify the encryption string/port to match the one used in the client. You may also want to whitelist an ip or two for security reasons. You can add more than one as in the following example: 

WHITELIST = ["192.168.1.1", "192.168.1.2", "192.168.1.3"]

Next will create a service for our python server so that it runs on boot / in the background.
```python
nano /etc/systemd/system/fail2networkban.service
```
Paste the following, modying the ExecStart path to point to the server.py file we just edited.
```
[Unit]
Description = Fail2NetworkBan
After = network.target # Assuming you want to start after network interfaces are made available
 
[Service]
Type = simple
ExecStart = python3 /path/to/server.py
User = root
Group = root
Restart = on-failure
SyslogIdentifier = fail2networkban.log
RestartSec = 5
TimeoutStartSec = infinity
 
[Install]
WantedBy = multi-user.target
```
Next we will Enable/Start our service so that it will run in the background.
```
systemctl enable fail2networkban
systemctl daemon-reload
systemctl start fail2networkban
```
Check that the service is running with "systemctl | grep running"

After this you should be up and running! 
# Troubleshooting

The following will help you find the issue:

1. Bans should be populating within /etc/pve/firewall/cluster.fw on the proxmox server. 
If they are not, check /var/log/fail2networkban.log
2. If /var/log/fail2networkban.log  exists and looks okay, report the issue with detailed information . If it contains errors, correct the issue. If it does not exist, run the server manually to determine why it's not working with  "python3 server.py" Report Issues.
3. Over on the client check the log /var/log/fail2networkban.log. If it contains errors, correct them. If it does not exist, check /var/log/fail2ban.log to determine if it had problems running the action. Last, run the client manually using python3 client.py "servicename" "ban" "192.168.1.254" to see error output/communication isses with the server. 

To manually unabn a client, in the case of a glitch/bug, you can modify nano /etc/pve/firewall/cluster.fw and remove the ip address from there. 

## License
[GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html)
