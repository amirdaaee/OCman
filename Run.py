#!/usr/bin/python3
import subprocess
import re
import os
import yaml

base_dir_path = os.path.dirname(os.path.realpath(__file__))
conf_file_path = os.path.join(base_dir_path, 'conf.yaml')
with open(conf_file_path, 'r') as ymlcfg:
    cfg = yaml.load(ymlcfg)

address_file = os.path.join(base_dir_path, 'server.address')
if not os.path.isfile(address_file):
    print('Creating server address file at ', address_file)
    with open(address_file, 'w') as _:
        pass

with open(address_file, 'r') as adds:
    adds = adds.read()
adds = adds.split('\n')
adds = [x.replace(' ', '').split(':') for x in adds if x.replace(' ', '') != '']
for c, i in enumerate(adds):
    if len(i) == 1:
        adds[c].append(cfg['personalize']['server-port_default'])
assert len(adds) > 0, 'No server is defined in {}'.format(address_file)

ping = cfg['personalize']['ping_default']
def_str = 'y/N'
if ping:
    def_str = 'Y/n'
ping_ = input('ping servers? {}:'.format(def_str))
ping_ = ping_.lower()
if ping_ == 'n':
    ping = False
elif ping_ == 'y':
    ping = True

for c, i in enumerate(adds):
    print(c, ':', i[0] + ':' + i[1], end=' ')
    if ping:
        command = "nping --tcp-connect --delay {} -c {} -p {} {}".format(cfg['personalize']['ping_delay'],
                                                                         cfg['personalize']['ping_count'],
                                                                         i[1],
                                                                         i[0])
        p = subprocess.run(command, shell=True, stdout=subprocess.PIPE).stdout
        p = re.findall(r"(Avg rtt: )(.+)(TCP)", str(p))
        try:
            print('--', p[0][1][:-2])
        except Exception as E:
            print('NA ({})'.format(E))
    else:
        print(' ')

while True:
    c = input('Which?')
    try:
        c = adds[int(c)]
        break
    except Exception as E:
        print(E)
adds = c[0] + ':' + c[1]
print('Connecting to', adds)
if cfg['auth']['username'] is None:
    print('no username is set')
    print('you can save username in {} at auth:username:'.format(conf_file_path))
    username = input('username :')
else:
    username = cfg['auth']['username']
    print('username :', username)

if cfg['auth']['pass'] is None:
    print('no password is set')
    print('you can save password in {} at auth:pass:'.format(conf_file_path))
    passw = input('password :')
else:
    passw = cfg['auth']['pass']

forw = cfg['personalize']['Port-Forward_default']
def_str = 'y/N'
if forw:
    def_str = 'Y/n'
forw_ = input('port forwarding? {}:'.format(def_str))
forw_ = forw_.lower()
if forw_ == 'n':
    forw = False
elif forw_ == 'y':
    forw = True

if forw:
    port = cfg['personalize']['forward_port']
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
