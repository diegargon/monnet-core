# Monnet Gateway

Mediates between the web UI and the system.

At this moment, currently only it is used for Ansible features.



## Install

monnet-gateway its installed in the same machine as the monnet web/UI

```
mkdir /opt/monnet-core

cd /opt/monnet-core

git clone https://github.com/diegargon/monnet-core.git

cp files/monnet-gateway.service  /etc/systemd/system

systemctl enable  monnet-gateway.service

systemctl start  monnet-gateway.service
```

## Configure Ansible Support

Ansible server listens on localhost only; it is a testing feature without security.
You must install ansible on the same system

```
apt install ansible
```

Ansible must output in JSON format.

```
nano /etc/ansible/ansible.cfg

[defaults]
stdout_callback=json
```

## Configure Client hosts for allow Ansible

By default, the Ansible SSH user will be 'ansible'.

Must be/have:

    * Be a sudo member without need to type a password
    * Have the public SSH key installed

Example

```
apt install sudo
adduser --disabled-password ansible
usermod -aG sudo ansible
```

Start 'visudo' and add:

```
ansible ALL=(ALL) NOPASSWD: ALL
```

# Fedora

```
sudo adduser ansible
sudo usermod -aG wheel ansible
```

You must have "Ansible Support" checked in the General configuration tab and "Ansible Support" in the host configuration section (Web UI).

## SSH CERTS

For the Ansible server be able to connect to the hosts, you need to generate an SSH key and install it on each host you want to access via MonNet/Ansible.

```
$ ssh-keygen -m PEM -t rsa -b 4096
$ ssh-copy-id -i ~/.ssh/id_rsa.pub ansible@ip.ip.ip.ip
```

The user must exist and must be allowed to log in with standard credentials to install the key (you can disable it after).

Or do it manually on the client host:

```
runuser -u ansible mkdir /home/ansible/.ssh
runuser -u ansible nano /home/ansible/.ssh/authorized_keys
```

And paste the SSH public key.

If you don't use ssh-copy-id you must manually add the key to the known_host file (Monnet server side).

```
ssh-keyscan -t ecdsa,ed25519 -H server.example.com >> ~/.ssh/known_hosts 2>&1
```

If the host fingerprint change you must first remove the old one

```
ssh-keygen -R
```

You can force Ansible to ignore the host fingerprint check.

```
[defaults]
host_key_checking = False
```


## Payload (probably outdated)

Receive

```
{
    "command": playbook
    "data": {
        "playbook": "mi_playbook.yml",
        "extra_vars": {
            "var1": "valor1",
            "var2": "valor2"
        },
        "ip": "192.168.1.100",
        "limit": "mi_grupo" #optional
        "user": "user" # optional
    }
}
```

## Netcat test examples

```
echo '{"command": "playbook", "data": {"playbook": "test.yml"}}' | nc localhost 65432
echo '{"command": "playbook", "data": {"playbook": "test.yml", "extra_vars": {"var1": "value1", "var2": "value2"}}}' | nc localhost 65432
echo '{"command": "playbook", "data": {"playbook": "ansible-ping.yml", "extra_vars": {}, "ip": "192.168.2.148"}}' | nc localhost 65432
echo '{"command": "playbook", "data": {"playbook": "ansible-ping.yml", "extra_vars": {}, "ip": "192.168.2.148", "user": "ansible"}}' | nc localhost 65432
```