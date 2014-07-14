# MongoDB on AWS using CloudFormation

This repo contains scripts and sample templates to deploy [MongoDB](http://www.mongodb.org) to [Amazon Web Services](http://aws.amazon.com) using [CloudFormation](http://aws.amazon.com/cloudformation/).

## Resources
`scripts`: Python scripts that build, deploy, test, and package MongoDB for the [AWS Marketplace](http://aws.amazon.com/marketplace). Instances are configured using [documented best practices](http://docs.mongodb.org/ecosystem/platforms/amazon-ec2/#deploy-mongodb-on-ec2).

`templates`: (DEPRECATED/BROKEN) Sample CloudFormation templates to bootstrap individual EC2 instances

## Usage

Clone the repo:

    $ git clone https://github.com/crcsmnky/aws-cfn-mongodb

Install requirements:

    $ pip install -r requirements.txt

Run the MongoDB Marketplace AMI Builder:

    $ python scripts/build-marketplace-ami.py --iops=1000 --security-group=[groupname] --keypair=[path/to/keypair.pem]

Run the MongoDB Marketplace AMI Cleanup:

    $ python scripts/cleanup.py --instance-id=[instance id]

## Builder Usage

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
        --enterprise                (BROKEN) Builds Marketplace AMI with MongoDB Enterprise
        --save-template             Saves the generated CloudFormation template to a file

    What This Script Does:
        build    ## builds CF template, returns template json
        deploy   ## deploys CF template, returns AWS CloudFormation StackId
        test     ## tests MongoDB EC2 instance, returns test output
        package  ## packages MongoDB AMI, returns AMI Id

## Notes
- Templates are broken! Do not use!

