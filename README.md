# Monnet Core

Monnet Gateway

## Install

```
mkdir /opt/monnet-core

cd /opt/monnet-core

git clone https://github.com/diegargon/monnet-core.git

cp files/monnet-gateway.service  /etc/systemd/system

systemctl enable  monnet-gateway.service

systemctl start  monnet-gateway.service
```
