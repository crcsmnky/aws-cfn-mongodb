# CFN Tools for MongoDB on AWS

Tools for deploying [MongoDB](http://www.mongodb.org) on [Amazon Web Services](http://aws.amazon.com) using [CloudFormation](http://aws.amazon.com/cloudformation/).

## Resources
`scripts`: scripts that configure MongoDB instances against [documented best practices](http://docs.mongodb.org/ecosystem/platforms/amazon-ec2/#deploy-mongodb-on-ec2)

`templates`: CloudFormation templates to bootstrap individual EC2 instances

## Usage

Clone the repo:

    $ git clone https://github.com/crcsmnky/aws-cfn-mongodb

Install the [AWS command line tools](http://aws.amazon.com/cli/):

    $ pip install awscli

Deploy a CloudFormation template:

    $ aws cloudformation create-stack --stack-name [NAME] --template-body file://[TEMPLATE FULL PATH] --parameters ParameterKey=SecurityGroupName,ParameterValue=[SECURITY GROUP] ParameterKey=KeyPairName,ParameterValue=[KEY PAIR] ParameterKey=InstanceType,ParameterValue=[INSTANCE TYPE]

## Notes
- Only m1.large, m1.xlarge, m2.xlarge, m2.2xlarge, m2.4xlarge are supported instance types
- The templates refer to the source Github repo when pulling the setup script - if you fork the repo, update the script location in the template ([line 63](https://github.com/crcsmnky/aws-cfn-mongodb/blob/master/templates/mongodb-2.4-1000-iops.json#L63))

