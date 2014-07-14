"""
MongoDB Marketplace AMI Builder

Build, deploy, test, and package MongoDB AMIs for the AWS Marketplace

Usage:
    build-marketplace-ami.py [options] --iops=<iops> --security-group=<group> ... --keypair=<keypath> [--keypair-name=<keyname>]
    build-marketplace-ami.py --help
    build-marketplace-ami.py --version

Arguments:
    --iops=<iops>               1000, 2000, or 4000 IOPS for data volume
    --security-group=<group>    Security group name for instance (use multiple times for multiple groups)
    --keypair=<keypath>         Path to keypair used to setup this instance
    --keypair-name=<keyname>    Name of keypair used to setup this instance (optional, defaults to basename of keypath)

Options:
    -h --help                   Show help
    --version                   Show version
    --enterprise                Builds Marketplace AMI with MongoDB Enterprise
    --save-template             Saves the generated CloudFormation template to a file

What This Script Does:
    build    ## builds CF template, returns template json
    deploy   ## deploys CF template, returns AWS CloudFormation StackId
    test     ## tests MongoDB EC2 instance, returns test output
    package  ## packages MongoDB AMI, returns AMI Id
"""

from troposphere import Ref, Template, Parameter, Output
from troposphere import Base64, FindInMap, GetAtt, Tags, Join
from docopt import docopt
import troposphere.ec2 as ec2
import boto.cloudformation.connection as cfconnection
import boto.ec2.connection as ec2connection
import boto.ec2.blockdevicemapping as ec2bdm
import os.path
from time import sleep
import fabfile
from datetime import datetime


REGION_AMI_MAP = {
    "us-east-1" :       {"AMI" : "ami-fb8e9292"},
    "us-west-2" :       {"AMI" : "ami-043a5034"},
    "us-west-1" :       {"AMI" : "ami-7aba833f"},
    "eu-west-1" :       {"AMI" : "ami-2918e35e"},
    "ap-southeast-1" :  {"AMI" : "ami-b40d5ee6"},
    "ap-northeast-1" :  {"AMI" : "ami-c9562fc8"},
    "ap-southeast-2" :  {"AMI" : "ami-3b4bd301"},
    "sa-east-1" :       {"AMI" : "ami-215dff3c"},
}


STORAGE_MAP = {
    1000 : {
        "data":    {"size": 200, "iops": 1000 },
        "journal": {"size": 25, "iops": 250 },
        "log":     {"size": 10, "iops": 100 },
    },
    2000 : {
        "data":    {"size": 200, "iops": 2000 },
        "journal": {"size": 25, "iops": 250 },
        "log":     {"size": 15, "iops": 150 },
    },
    4000 : {
        "data":    {"size": 400, "iops": 4000 },
        "journal": {"size": 25, "iops": 250 },
        "log":     {"size": 20, "iops": 200 },
    },
}


MONGODB_VERSION = "2.6.3"
AWS_MARKETPLACE_ACCOUNT = "679593333241"


def build_template(instance_type="m3.xlarge", keypair=None, groups=["default"], setup_script="instance-setup.sh", iops=1000, enterprise=False):
    print("## Building CloudFormation Template")

    template = Template()

    ## CF Template Parameters for Community vs. Standard
    if enterprise is False:
        repopath = "/etc/yum.repos.d/mongodb.repo"
        repocontent = [
            "[MongoDB]\n",
            "name=MongoDB Repository\n",
            "baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/x86_64\n",
            "gpgcheck=0\n",
            "enabled=1\n"
        ]
        shortname = "MongoDBInstance"
        longname = "MongoDB {version} {iops} IOPS".format(version=MONGODB_VERSION, iops=iops)
    else:
        repopath = "/etc/yum.repos.d/mongodb-enterprise.repo"
        repocontent = [
            "[MongoDB-Enterprise]\n",
            "name=MongoDB Enterprise Repository\n",
            "baseurl=https://repo.mongodb.com/yum/redhat/6/mongodb-enterprise/stable/$basearch/\n",
            "gpgcheck=0\n",
            "enabled=1\n"
        ]
        shortname = "MongoDBStandardInstance"
        longname = "MongoDB Standard {version} {iops} IOPS".format(version=MONGODB_VERSION, iops=iops)

    ## CF Template UserData script
    ## Hack up UserData a bit so refs are setup correctly
    user_data = [
        "#!/bin/bash\n",
        "yum update -y aws-cfn-bootstrap\n",
        "/opt/aws/bin/cfn-init -v -s ",
            Ref("AWS::StackName"),
            " -r ", shortname, " --region ",
            Ref("AWS::Region"),
            " > /tmp/cfn-init.log 2>&1\n"
    ]
    with open(setup_script) as lines:
        for line in lines:
            user_data.append(line)

    ## CF Template Block Device Mappings
    block_device_mappings = []
    for mount,type in {"/dev/xvdf": "data", "/dev/xvdg": "journal", "/dev/xvdh": "log"}.items():
        block_device_mappings.append(
            ec2.BlockDeviceMapping(
                DeviceName = mount,
                Ebs = ec2.EBSBlockDevice(
                    VolumeSize = STORAGE_MAP[iops][type]["size"],
                    Iops = STORAGE_MAP[iops][type]["iops"],
                    VolumeType = "io1",
                    DeleteOnTermination = False,
                ),
            )
        )

    ## CF Template Region-AMI-Mapping
    template.add_mapping("RegionAMIMap", REGION_AMI_MAP)

    ## CF Template EC2 Instance
    mongodb_instance = template.add_resource(ec2.Instance(
        shortname,
        ImageId = FindInMap("RegionAMIMap", Ref("AWS::Region"), "AMI"),
        InstanceType = instance_type,
        KeyName = keypair,
        SecurityGroups = groups,
        EbsOptimized = True,
        BlockDeviceMappings = block_device_mappings,
        Metadata = {
            "AWS::CloudFormation::Init" : {
                "config" : {
                    "files" : {
                        repopath : {
                            "content" : { "Fn::Join" : ["", repocontent ] },
                            "mode" : "000644",
                            "owner" : "root",
                            "group" : "root"
                        }
                    }
                }
            }
        },
        UserData = Base64(Join("", user_data)),
        Tags = Tags(
            Name = longname,
        ),
    ))

    ## CF Template Outputs
    template.add_output([
        Output(
            "MongoDBInstanceID",
            Description = "MongoDBInstance ID",
            Value = Ref(mongodb_instance)
        ),
        Output(
            "MongoDBInstanceDNS",
            Description = "MongoDBInstance Public DNS",
            Value = GetAtt(mongodb_instance, "PublicDnsName")
        )
    ])

    print("## CloudFormation Template Built")

    return template.to_json()


def deploy_template(template, enterprise=False, iops=1000):
    print("## Deploying CloudFormation Template")

    if enterprise is False:
        stackname = "MongoDB-26-{iops}-IOPS".format(iops=iops)
    else:
        stackname = "MongoDB-Standard-26-{iops}-IOPS".format(iops=iops)

    cfcn = cfconnection.CloudFormationConnection()
    stackid = cfcn.create_stack(stack_name=stackname, template_body=template)

    print("## CloudFormation Template Deployed")
    return stackid


def wait_for_create(stackid):
    print("## Waiting for Stack Creation (5m)")
    sleep(300)
    cfcn = cfconnection.CloudFormationConnection()
    stack = cfcn.describe_stacks(stackid)[0]
    if stack.stack_status != 'CREATE_COMPLETE':
        print("## Stack Creation Failure, Bailing...")
        sys.exit(-1)
    else:
        print("## Stack Created")


def test_instance(stackid, sshkey):
    print("## Testing Instance")

    print("### Get Instance ID from CloudFormation")
    cfcn = cfconnection.CloudFormationConnection()
    stack = cfcn.describe_stacks(stackid)[0]
    resource = stack.list_resources()[0]
    instanceid = resource.physical_resource_id

    print("### Get Public DNS Name of Instance")
    ec2cn = ec2connection.EC2Connection()
    instance = ec2cn.get_only_instances(instanceid)[0]
    dnsname = instance.public_dns_name

    print("### Setup Fabric")
    fabfile.env.host_string = dnsname
    fabfile.env.user = 'ec2-user'
    fabfile.env.key_filename = sshkey
    fabfile.env.disable_known_hosts = True

    print("### Run Fabric Functions")
    fabfile.check_mount_points()
    fabfile.check_package_install()
    fabfile.check_readahead()
    fabfile.check_config()
    fabfile.check_keepalive()
    fabfile.check_zone_reclaim()
    fabfile.check_ulimits()
    fabfile.check_mmsagent()
    fabfile.cleanup()

    print("## Testing Completed")


def package(stackid, iops=1000, enterprise=False):
    print("## Packaging Instance")

    print("### Get Instance ID from CloudFormation")
    cfcn = cfconnection.CloudFormationConnection()
    stack = cfcn.describe_stacks(stackid)[0]
    resource = stack.list_resources()[0]
    instanceid = resource.physical_resource_id

    print("### Get Instance Information from EC2")
    ec2cn = ec2connection.EC2Connection()
    instance = ec2cn.get_only_instances(instanceid)[0]

    if enterprise is False:
        name = "MongoDB {version} {iops} IOPS".format(version=MONGODB_VERSION, iops = iops)
        description = "MongoDB {version} {iops} IOPS".format(version=MONGODB_VERSION, iops = iops)
    else:
        name = "MongoDB Standard {version} {iops} IOPS".format(version=MONGODB_VERSION, iops = iops)
        description = "MongoDB Standard {version} {iops} IOPS".format(version=MONGODB_VERSION, iops = iops)

    print("### Creating AMI For Instance {instanceid}".format(instanceid=instanceid))
    imageid = ec2cn.create_image(
        instanceid, name, description,
        no_reboot = False,
        block_device_mapping = instance.block_device_mapping
    )

    print("### Instance AMI Created {imageid}".format(imageid=imageid))
    print("## Packaging Complete")

    return imageid


def main():
    args = docopt(__doc__, version="MongoDB Marketplace AMI Builder 1.0")

    if args['--keypair-name'] is None:
        keyname = os.path.basename(args['--keypair'])
        if '.pem' in keyname:
            keyname = keyname[0:keyname.find('.pem')]
    else:
        keyname = args['--keypair-name']

    security_groups = args['--security-group']
    iops = int(args['--iops'])
    enterprise = args['--enterprise']
    save_template = args['--save-template']

    print("# MongoDB Marketplace AMI Builder 1.0")
    if enterprise is False:
        print("# Building MongoDB {version} {iops} IOPS AMI".format(
            version=MONGODB_VERSION, iops=iops))
    else:
        print("# Building MongoDB {version} Standard {iops} IOPS AMI".format(
            version=MONGODB_VERSION, iops=iops))

    template = build_template(
        keypair=keyname,
        iops=iops,
        groups=security_groups,
        enterprise=enterprise
    )

    if save_template is True:
        if enterprise is False:
            fname = "mongodb-{version}-{iops}-{date}.json".format(
                version=MONGODB_VERSION,iops=iops,date=datetime.now().isoformat())
        else:
            fname = "mongodb-standard-{version}-{iops}-{date}.json".format(
                version=MONGODB_VERSION,iops=iops,date=datetime.now().isoformat())

        ftemplate = open(fname, 'w')
        ftemplate.write(template)
        ftemplate.close()


    stackid = deploy_template(
        template,
        enterprise=enterprise,
        iops=iops
    )

    wait_for_create(
        stackid
    )

    test_instance(
        stackid,
        args['--keypair']
    )

    ami_id = package(
        stackid,
        iops=iops,
        enterprise=enterprise
    )

    # share(ami_id)

if __name__ == '__main__':
    main()