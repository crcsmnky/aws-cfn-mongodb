from fabric.api import run, env

def check_mount_points():
    run("sudo mount | grep 'xvd'")

def check_package_install():
    run("sudo yum list installed | grep 'mongodb'")

def check_readahead():
    run("sudo blockdev --report")
    run("cat /etc/udev/rules.d/85-ebs.rules")

def check_config():
    run("cat /etc/mongod.conf")

def check_keepalive():
    run("grep 'keepalive' /etc/sysctl.conf")
    run("cat /proc/sys/net/ipv4/tcp_keepalive_time")

def check_zone_reclaim():
    run("cat /proc/sys/vm/zone_reclaim_mode")

def check_ulimits():
    run("cat /etc/security/limits.conf | grep 'mongod'")
    run("cat /etc/security/limits.d/90-nproc.conf | grep 'mongod'")

def check_mmsagent():
    run("ls -al /usr/local | grep 'mms-agent'")
    run("python -c 'import pymongo'")

def cleanup():
    run("rm ~/.ssh/authorized_keys")
    run("sudo rm /root/.ssh/authorized_keys")
    run("cat /dev/null > ~/.bash_history")
    run("history -c")
