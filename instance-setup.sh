
## Send all output to log
exec 2> /tmp/mongodb-instance-setup.log
exec >> /tmp/mongodb-instance-setup.log

## Update installed packages
yum -y update

## Install MongoDB based on included repo
if [ -f /etc/yum.repos.d/mongodb.repo ]; then
    yum -y install mongodb-org
elif [ -f /etc/yum.repos.d/mongodb-enterprise.repo ]; then
    yum -y install mongodb-enterprise
fi

## Waiting for EBS mounts to become available
while [ ! -e /dev/xvdf ]; do echo waiting for /dev/xvdf to attach; sleep 5; done
while [ ! -e /dev/xvdg ]; do echo waiting for /dev/xvdg to attach; sleep 5; done
while [ ! -e /dev/xvdh ]; do echo waiting for /dev/xvdh to attach; sleep 5; done

## Setup Storage
mkdir /data /log /journal

for i in f g h; do mkfs.ext4 /dev/xvd$i; done

echo '/dev/xvdf /data ext4 defaults,auto,noatime,noexec 0 0' >> /etc/fstab
echo '/dev/xvdg /journal ext4 defaults,auto,noatime,noexec 0 0' >> /etc/fstab
echo '/dev/xvdh /log ext4 defaults,auto,noatime,noexec 0 0' >> /etc/fstab

for i in data log journal; do mount /$i; done

chown mongod:mongod /data /log /journal

ln -s /journal /data/journal

for i in f g h; do blockdev --setra 32 /dev/xvd$i; done

## Persist read ahead settings
# echo 'ACTION==\"add\" KERNEL==\"xvdf\" ATTR{bdi/read_ahead_kb}=\"16\"' >> /etc/udev/rules.d/85-ebs.rules
# echo 'ACTION==\"add\" KERNEL==\"xvdg\" ATTR{bdi/read_ahead_kb}=\"16\"' >> /etc/udev/rules.d/85-ebs.rules
# echo 'ACTION==\"add\" KERNEL==\"xvdh\" ATTR{bdi/read_ahead_kb}=\"16\"' >> /etc/udev/rules.d/85-ebs.rules
cat <<EOF>> /etc/udev/rules.d/85-ebs.rules
SUBSYSTEM=="block", ACTION=="add|change", ATTR{bdi/read_ahead_kb}="16", ATTR{queue/scheduler}="noop"
EOF

## Update MongoDB Configuration
cat <<EOF > /etc/mongod.conf
logpath=/log/mongod.log
fork=true
dbpath=/data
EOF

chkconfig mongod off

## Update System Settings

# NUMA
sed -i '/^kernel/ s/$/ numa=off/g' /etc/grub.conf
echo 'vm.zone_reclaim_mode = 0' >> /etc/sysctl.conf
echo 0 > /proc/sys/vm/zone_reclaim_mode

# Transparent HugePages
if test -f /sys/kernel/mm/transparent_hugepage/enabled; then
   echo madvise > /sys/kernel/mm/transparent_hugepage/enabled
fi
if test -f /sys/kernel/mm/transparent_hugepage/defrag; then
   echo madvise > /sys/kernel/mm/transparent_hugepage/defrag
fi

# TCP KeepAlive
echo 'net.ipv4.tcp_keepalive_time = 300' >> /etc/sysctl.conf
echo 300 > /proc/sys/net/ipv4/tcp_keepalive_time

# Ulimits
echo 'mongod soft nofile 64000' >> /etc/security/limits.conf
echo 'mongod hard nofile 64000' >> /etc/security/limits.conf
echo 'mongod soft nproc 32000' >> /etc/security/limits.conf
echo 'mongod hard nproc 32000' >> /etc/security/limits.conf

echo 'mongod soft nproc 32000' >> /etc/security/limits.d/90-nproc.conf
echo 'mongod hard nproc 32000' >> /etc/security/limits.d/90-nproc.conf

## Start MongoDB
service mongod start

## Install MMS Monitoring Agent
curl -OL https://mms.mongodb.com/download/agent/monitoring/mongodb-mms-monitoring-agent-latest.x86_64.rpm
rpm -U mongodb-mms-monitoring-agent-latest.x86_64.rpm
