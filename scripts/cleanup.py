"""
MongoDB Marketplace AMI Cleanup

Cleanup after building AWS Marketplace AMIs (terminate instance, delete volumes)

Usage:
    cleanup.py [options] --instance-id=<instance-id>

Arguments:
    --instance-id=<instance-id>     1000, 2000, or 4000 IOPS for data volume

Options:
    -h --help                       Show help
    --keep-volumes                  Don't delete attached volumes

What This Script Does:
    Terminates the specified instance (by instance-id) and deletes PIOPS EBS volumes
"""

from docopt import docopt
import boto.ec2.connection as ec2connection
from time import sleep

def cleanup(instanceid, delete_volumes=True):
    print("## Cleanup Instance {instanceid}".format(instanceid=instanceid))

    print("### Getting Instance Information from EC2")
    ec2cn = ec2connection.EC2Connection()

    print("### Getting Volume Information for Instance {instanceid}".format(instanceid=instanceid))
    volumes = [v for v in ec2cn.get_all_volumes() if v.attach_data.instance_id == instanceid]

    print("### Terminating Instance {instanceid}".format(instanceid=instanceid))
    ec2cn.terminate_instances(instance_ids=[instanceid])

    print("### Waiting for Instance Termination")
    sleep(60)

    if delete_volumes:
        for volume in volumes:
            print("### Deleting Volume {volumeid}").format(volumeid=v.id)
            try:
                volume.delete()
            except Exception, e:
                print(e)

    print("## Cleanup Complete")


def main():
    args = docopt(__doc__, version="MongoDB Marketplace AMI Cleanup 1.0")

    instanceid = args['--instance-id']
    delete_volumes = not args['--keep-volumes']

    cleanup(instanceid, delete_volumes)


if __name__ == '__main__':
    main()