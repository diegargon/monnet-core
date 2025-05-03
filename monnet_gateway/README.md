# Monnet Gateway

Mediates between the web UI (Monnet) and the system.

At this moment, it is currently only used for Ansible features.

## Install

Monnet Gateway is installed on the same machine as the Monnet web/UI.

In this example, we are using Debian 12.

```
apt install python3.11-venv
mkdir /opt/monnet-core
cd /opt/
git clone https://github.com/diegargon/monnet-core.git
cd monnet-core/monnet_gateway
chmod +x install.bash
./install.bash
```

The install script sets up a virtual Python environment for an application in a specific directory (/opt/monnet-core/monnet_gateway).
It configures a systemd service by copying a configuration file and setting the proper permissions. Finally, it configures Ansible to use JSON-formatted output by modifying its configuration file.

Also, install `requirements.txt` within the virtual environment.

## Upgrading

Use `update.bash`, which will sync the git repo and perform the necessary tasks.

```
cd monnet-core/monnet_gateway
chmod +x install.bash
./install.bash
```

## Configure Monnet Gateway access to the database

```
/etc/monnet/config-db.json
{
    "host": "localhost",
    "port": 3306,
    "database": "monnet",
    "user": "usuario",
    "password": "mypass",
    "python_driver": "mysql-connector"
}
```

## Configure Ansible Support

The Ansible server listens on localhost only; you must install Ansible on the same system.

```
apt install ansible
```

Ansible must output in JSON format.

```
nano /etc/ansible/ansible.cfg

[defaults]
stdout_callback=json
```

The directory for custom playboks is /var/lib/monnet/playbooks

Playbooks must begin with some @metadata on the begin of the playbook,

You can check /opt/monnet-core/monnet_gateway/playbooks for examples.


## Configure Client Hosts to allow Ansible connection

By default, the Ansible SSH user will be 'ansible'.

Must:

    * Be a sudo member without needing to type a password
    * Have the public SSH key installed

Example:

```
apt install sudo
adduser --disabled-password ansible
usermod -aG sudo ansible
```

Start 'visudo' and add:

```
ansible ALL=(ALL) NOPASSWD: ALL
```

## Fedora

```
sudo adduser ansible
sudo usermod -aG wheel ansible
```

You must have "Ansible Support" checked in the General configuration tab and "Ansible Support" in the host configuration section (Web UI).

## SSH CERTS

For the Ansible server to connect to the hosts, you need to generate an SSH key and install it on each host you want to access via MonNet/Ansible.

```
$ ssh-keygen -m PEM -t rsa -b 4096
$ ssh-copy-id -i ~/.ssh/id_rsa.pub ansible@ip.ip.ip.ip
```

The user must exist and must be allowed to log in with standard credentials to install the key (you can disable it afterward).

Or do it manually on the client host:

```
runuser -u ansible mkdir /home/ansible/.ssh
runuser -u ansible nano /home/ansible/.ssh/authorized_keys
```

And paste the SSH public key.

If you don't use `ssh-copy-id`, you must manually add the key to the known_hosts file (Monnet server side).

```
ssh-keyscan -t ecdsa,ed25519 -H server.example.com >> ~/.ssh/known_hosts 2>&1
```

Otherwise, you will get a connection error refused.

If the host fingerprint changes, you must first remove the old one.

```
ssh-keygen -R
```

You can force Ansible to ignore the host fingerprint check.

```
[defaults]
host_key_checking = False
```

## Playbooks Vars

Playbooks may sometimes require variables. These variables are stored in the database, and passwords or any critical information must be stored encrypted.

The current mechanism uses a public/private key pair.
In the UI, the data is encrypted with the public key, and Monnet Gateway uses the private key when it needs to decrypt it. To achieve this, the keys must be generated.

Generating the keys:

```
openssl genpkey -algorithm RSA -out monnet_private_key.pem -pkeyopt rsa_keygen_bits:2048
openssl rsa -in monnet_private_key.pem -pubout -out monnet_public_key.pem
```

Install Private Key:

```
mkdir -p /etc/monnet/certs-priv
chown root:root /etc/monnet/certs-priv
chmod 700 /etc/monnet/certs-priv
mv monnet_private_key.pem /etc/monnet/certs-priv
chmod 600 /etc/monnet/certs-priv/monnet_private_key.pem
```

Install Public Key:

```
mkdir -p /etc/monnet/certs-pub
chown root:root /etc/monnet/certs-pub
chmod 755 /etc/monnet/certs-pub
mv monnet_public_key.pem /etc/monnet/certs-pub
chmod 644 /etc/monnet/certs-pub/monnet_public_key.pem
```

Likewise, we must copy the contents of the public key file and insert it into the UI under Configuration -> Security -> Encrypt Public Key.

# Technical Info

## Payload (probably outdated)

Receive:

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

## Netcat Test Examples

```
echo '{"command": "playbook", "data": {"playbook": "test.yml"}}' | nc localhost 65432
echo '{"command": "playbook", "data": {"playbook": "ansible-ping.yml", "ip": "192.168.2.148"}}' | nc localhost 65432
echo '{"command": "playbook", "data": {"playbook": "ansible-ping.yml", "ip": "192.168.2.148", "user": "ansible"}}' | nc localhost 65432
```