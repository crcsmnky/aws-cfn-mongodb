from fabric.api import *

@task
def check_mount_points():
    sudo("mount | grep 'xvd'")

@task
def check_package_install():
    sudo("yum list installed | grep 'mongodb'")

@task
def check_readahead():
    sudo("blockdev --report")
    run("cat /etc/udev/rules.d/85-ebs.rules")

@task
def check_config():
    run("cat /etc/mongod.conf")

@task
def check_datadir():
    run("ls -l /data")

@task
def check_keepalive():
    run("grep 'keepalive' /etc/sysctl.conf")
    run("cat /proc/sys/net/ipv4/tcp_keepalive_time")

@task
def check_zone_reclaim():
    run("cat /proc/sys/vm/zone_reclaim_mode")
    run("grep 'zone_reclaim_mode' /etc/sysctl.conf")

@task
def check_thp():
    run("cat /sys/kernel/mm/transparent_hugepage/enabled")
    run("cat /sys/kernel/mm/transparent_hugepage/defrag")

@task
def check_ulimits():
    run("cat /etc/security/limits.conf | grep 'mongod'")
    run("cat /etc/security/limits.d/90-nproc.conf | grep 'mongod'")

@task
def check_service():
    sudo("service --status-all | grep mongod")

@task
def check_chkconfig():
    sudo("chkconfig | grep mongod")

@task
def check_mmsagent():
    sudo("yum list installed | grep 'mongodb-mms'")

@task
def cleanup():
    run("rm ~/.ssh/authorized_keys")
    sudo("rm /root/.ssh/authorized_keys")
    run("cat /dev/null > ~/.bash_history")
    run("history -c")
