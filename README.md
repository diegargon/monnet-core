# Monnet Core

Monnet Gateway

## Install

```
mkdir /opt/monnet-gateway

cd /opt/monnet-gateway

git clone https://github.com/diegargon/monnet-gateway.git

cp files/monnet-gateway.service  /etc/systemd/system

systemctl enable  monnet-gateway.service

systemctl start  monnet-gateway.service
```
