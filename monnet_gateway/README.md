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
    "dbhost": "localhost",
    "dbport": 3306,
    "dbname": "monnet",
    "dbuser": "username",
    "dbpassword": "mydbpass",
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


## Playbook Metadata

Playbooks must include metadata at the beginning of the file. This metadata is used by Monnet Gateway to identify and manage playbooks. The metadata should be written as YAML comments and must include at least the following fields:

- `id` (required): A unique identifier for the playbook.
- `name` (required): A descriptive name for the playbook.

### Optional Metadata Fields

- `description`: A brief description of what the playbook does.
- `os`: A list of operating systems the playbook is compatible with (e.g., `["linux", "windows"]`).
- `tags`: A list of tags to categorize the playbook (e.g., `["system", "logs", "std"]`).
- `vars`: A list of variables the playbook uses, including their types, defaults, and descriptions.
- `requires`: Specific requirements for the playbook, such as minimum Ansible version or dependencies.
- `dependencies`: External libraries or tools required for the playbook to function.

### Example Metadata

```
# @meta
# id: example_playbook
# name: Example Playbook
# description: This is an example playbook with metadata.
# os: ["linux", "posix"]
# tags: ["example", "demo"]
# vars:
#   - name: example_var
#     type: str
#     default: "default_value"
#     description: "An example variable"
#     required: yes
# requires:
#   - ansible_version: "2.9"
# dependencies:
#   - library_name: ">=1.0.0"
---
- hosts: all
  tasks:
    - name: Example task
      debug:
        msg: "This is an example task."
```

### Notes

- The metadata block must start with `# @meta` and be placed before the playbook content.
- While only `id` and `name` are mandatory, including additional fields like `description`, `os`, and `tags` improves playbook organization and usability.
- Use `vars` to document variables required by the playbook, including their types and default values.
- The `requires` and `dependencies` fields help ensure the playbook is executed in a compatible environment.


## Payload (probably outdated)

Receive:

```
{
    "command": playbook
    "data": {
        "playbook": "mi-playbook-id",
        "ip": "192.168.1.100",
        "limit": "mi_grupo"             # Optional (not impemented)
        "user": "user"                  # Default ansible
    }
}
```

## Netcat Test Examples

```
echo '{"command": "playbook", "data": {"playbook": "test.yml"}}' | nc localhost 65432
echo '{"command": "playbook", "data": {"playbook": "ansible-ping.yml", "ip": "192.168.2.148"}}' | nc localhost 65432
echo '{"command": "playbook", "data": {"playbook": "ansible-ping.yml", "ip": "192.168.2.148", "user": "ansible"}}' | nc localhost 65432
```

# External Resources

- MAC address, latest oui.csv

    https://regauth.standards.ieee.org/standards-ra-web/pub/view.html