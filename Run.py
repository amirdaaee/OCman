#!/usr/bin/python3
import subprocess
import re
import os
import yaml
from multiprocessing.pool import ThreadPool

# ---------------- Directory preparing
base_dir_path = os.path.dirname(os.path.realpath(__file__))
conf_file_path = os.path.join(base_dir_path, 'conf.yaml')
auth_file_path = os.path.join(base_dir_path, 'auth.yaml')
server_file_path = os.path.join(base_dir_path, 'server.address')
# ---------------- Load configs
with open(conf_file_path, 'r') as ymlcfg:
    cfg = yaml.safe_load(ymlcfg)
# ---------------- Load authentication data
if not os.path.isfile(auth_file_path):
    print('Creating auth template at ', auth_file_path)
    with open(auth_file_path, 'w') as f:
        yaml.safe_dump({'username': None, 'password': None}, f)
with open(auth_file_path, 'r') as ymlauth:
    auth = yaml.safe_load(ymlauth)
# ---------------- Load Servers
if not os.path.isfile(server_file_path):
    print('Creating server address file at ', server_file_path)
    with open(server_file_path, 'w') as _:
        pass
with open(server_file_path, 'r') as adds:
    adds = adds.read()
adds = adds.split('\n')
adds = [x.replace(' ', '').split(':') for x in adds if x.replace(' ', '') != '']
for c, i in enumerate(adds):
    if len(i) == 1:
        adds[c].append(cfg['server-port_default'])
assert len(adds) > 0, 'No server is defined in {}'.format(server_file_path)
# ---------------- Ping servers
ping = cfg['ping_default']
def_str = 'y/N'
if ping:
    def_str = 'Y/n'
ping_ = input('ping servers? {}:'.format(def_str))
ping_ = ping_.lower()
if ping_ == 'n':
    ping = False
elif ping_ == 'y':
    ping = True
# .............
if ping:
    def ping_time(addr):
        command_ = "nping --tcp-connect --delay {} -c {} -p {} {}".format(cfg['ping_delay'],
                                                                          cfg['ping_count'],
                                                                          addr[1],
                                                                          addr[0])
        p_ = subprocess.run(command_, shell=True, stdout=subprocess.PIPE).stdout
        p_ = re.findall(r"(Avg rtt: )(.+)(TCP)", str(p_))
        try:
            return p_[0][1][:-2]
        except Exception as E_:
            return str(E_)


    with ThreadPool(max(len(adds), int(cfg['max_ping_threads']))) as tpool:
        latency = tpool.map(ping_time, adds)
# ---------------- Print Server list
for c, i in enumerate(adds):
    s_ = str(c) + ') ' + i[0] + ':' + i[1]
    print(s_, end='')
    if ping:
        s_ = cfg['server_ping_spaces'] - len(s_)
        print(' ' * s_, end='')
        print(latency[c])
    else:
        print('')
# ---------------- Get desired server
while True:
    c = input('Which?')
    try:
        c = adds[int(c)]
        break
    except Exception as E:
        print(E)
adds = c[0] + ':' + c[1]
print('Connecting to', adds)
# ---------------- authentication Data
if auth['username'] is None:
    print('no username is set')
    print('you can save username in {} at username:'.format(auth_file_path))
    username = input('username:')
else:
    username = auth['username']
    print('username:', username)

if auth['password'] is None:
    print('no password is set')
    print('you can save password in {} at password:'.format(auth_file_path))
    passw = input('password:')
else:
    passw = auth['password']
# ---------------- Set running mode
forw = cfg['Port-Forward_default']
def_str = 'y/N'
if forw:
    def_str = 'Y/n'
forw_ = input('port forwarding? {}:'.format(def_str))
forw_ = forw_.lower()
if forw_ == 'n':
    forw = False
elif forw_ == 'y':
    forw = True
# ---------------- Run
if forw:
    port = cfg['forward_port']
    print("Port-Forward :", port)
    print('-' * 50)
    command = 'printf "%s\\n" yes {} | openconnect --script-tun   --script   "ocproxy   -D   9055" -u {} {}'.format(
        passw, username, adds)
else:
    print('system wide proxy')
    subprocess.run('sudo echo "sudo access granted"', shell=True)
    print('-' * 50)
    command = 'printf "%s\\n" yes {} | sudo openconnect -u {} {}'.format(passw, username, adds)
subprocess.run(command, shell=True)
