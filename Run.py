#!/usr/bin/python3
import os
import re
import subprocess
from multiprocessing.pool import ThreadPool

import yaml


def get_or_default(prop, message):
    val = cfg[prop]
    def_str = 'y/N'
    if val:
        def_str = 'Y/n'
    val_ = input(f'{message} {def_str}:')
    val_ = val_.lower()
    if val_ == 'n':
        val = False
    elif val_ == 'y':
        val = True
    return val


# ---------------- Directory preparing
base_dir_path = os.path.dirname(os.path.abspath(__file__))
conf_file_path = os.path.join(base_dir_path, 'conf.yaml')
auth_file_path = os.path.join(base_dir_path, 'auth.yaml')
server_file_path = os.path.join(base_dir_path, 'server.address')
# ---------------- Load configs
if not os.path.isfile(conf_file_path):
    print('Creating config template at ', conf_file_path)
    config_template = {
        'ping_default': True,
        'Port-Forward_default': True,
        'forward_port': 9055,
        'keepalive_interval': 10,
        'server-port_default': 443,
        'ping_count': 3,
        'ping_delay': 0.1,
        'max_ping_threads': 15,
        'server_ping_spaces': 30,
        'openconnect-args': ''
    }
    with open(conf_file_path, 'w') as f:
        yaml.safe_dump(config_template, f)
with open(conf_file_path, 'r') as ymlcfg:
    cfg = yaml.safe_load(ymlcfg)
# ---------------- Load authentication data
if not os.path.isfile(auth_file_path):
    print('Creating auth template at ', auth_file_path)
    auth_template = {'username': None, 'password': None}
    with open(auth_file_path, 'w') as f:
        yaml.safe_dump(auth_template, f)
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
adds = [x.strip().split(':') for x in adds if x.replace(' ', '') != '']
for c, i in enumerate(adds):
    if len(i) == 1:
        adds[c].append(cfg['server-port_default'])
server_template = '\nserver1_ip:server1_port\nserver2_ip:server2_port'
assert len(adds) > 0, f'No server is defined in {server_file_path}. example:{server_template}'
# ---------------- Ping servers
ping = get_or_default('ping_default', 'ping servers?')
if ping:
    def ping_time(addr):
        command_ = f"nping --tcp-connect --delay {cfg['ping_delay']} -c {cfg['ping_count']} -p {addr[1]} {addr[0]}"
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
    print(f'you can save username in {auth_file_path} at username:')
    username = input('username:')
else:
    username = auth['username']
    print('username:', username)

if auth['password'] is None:
    print('no password is set')
    print(f'you can save password in {auth_file_path} at password:')
    passw = input('password:')
else:
    passw = auth['password']
# ---------------- Set running mode
forw = get_or_default('Port-Forward_default', 'port forwarding?')
pre_str = 'printf "%s\\n" yes '
post_str = f' -u {username}  {adds} '
oa = cfg['openconnect-args']
if forw:
    port = cfg['forward_port']
    ka = cfg['keepalive_interval']
    print("Port-Forward :", port)
    print('-' * 50)
    tune = f' --script-tun --script "ocproxy -D {port} -k {ka}" '
    command = f'{pre_str}{passw} | openconnect {tune} {oa} {post_str}'
else:
    print('system-wide proxy')
    subprocess.run('sudo echo "sudo access granted"', shell=True)
    print('-' * 50)
    command = f'{pre_str}{passw} | sudo openconnect {oa} {post_str}'
subprocess.run(command, shell=True)
