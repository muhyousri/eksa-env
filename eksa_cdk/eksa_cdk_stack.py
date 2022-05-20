import os.path
from constructs import Construct
from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_ssm as ssm,
    App, Stack , CfnOutput
)



class EksaCdkStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        envTagName = 'EKSDemoEnvironment'
        userdata_file = open("./user-data.sh", "rb").read()
        userdata = ec2.UserData.for_linux()
        userdata.add_commands(str(userdata_file, 'utf-8'))


        vpc = ec2.Vpc(self, "VPC",
        nat_gateways=0,
        subnet_configuration=[ec2.SubnetConfiguration(name="demo",cidr_mask=24,subnet_type=ec2.SubnetType.PUBLIC)]
        )

        
        role = iam.Role(self, "Role", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))


        instance = ec2.Instance(self, "DemoInstance",
            instance_type=ec2.InstanceType("t3a.large"),
            machine_image=ec2.MachineImage.latest_amazon_linux(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX,
                                                              edition=ec2.AmazonLinuxEdition.STANDARD,
                                                              virtualization=ec2.AmazonLinuxVirt.HVM,
                                                              storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE),
            vpc = vpc,
            role = role,
            user_data=userdata,
            instance_name = envTagName ,
            block_devices=[ec2.BlockDevice(
            device_name="/dev/xvda",
            volume=ec2.BlockDeviceVolume.ebs(50)
            )
            ]
        )

        cfn_document = ssm.CfnDocument(self, "Document", document_type="Command", name="SSMRunCommand",
             content= {
                "schemaVersion": '2.2',
                "mainSteps": [
                  {
                    "action": "aws:runDocument",
                    "name": 'Install_Docker',
                    "inputs": {
                      "documentType": 'SSMDocument',
                      "documentPath": 'AWS-ConfigureDocker',
                      "documentParameters": '{"action": "Install"}'
                    }
                  },
                  {
                    "action": 'aws:runDocument',
                    "name": 'Create_User',
                    "inputs": {
                      "documentType": 'SSMDocument',
                      "documentPath": 'AWSFleetManager-CreateUser',
                      "documentParameters": '{"UserName": "ssm-user", "CreateHomeDir": "Yes", "PerformAction": "Yes"}'
                    }
                  },
                  {
                    "action": 'aws:runDocument',
                    "name": 'Add_User_To_Docker_Group',
                    "inputs": {
                      "documentType": 'SSMDocument',
                      "documentPath": 'AWSFleetManager-AddUsersToGroups',
                      "documentParameters": '{"Groups": "docker", "Users": "ssm-user", "PerformAction": "Yes"}'
                    }
                  },
                  {
                    "action": 'aws:runShellScript',
                    "name": 'Kubectl_Install',
                    "inputs": {
                      "runCommand": [
                        'curl -o /usr/local/bin/kubectl -LO \"https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl\"',
                        'chmod +x /usr/local/bin/kubectl'
                      ]
                    }
                  },
                  {
                    "action": 'aws:runShellScript',
                    "name": 'Eksctl_Install',
                    "inputs": {
                      "runCommand": [
                        'curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp',
                        'mv -v /tmp/eksctl /usr/local/bin'
                      ]
                    }
                  },
                  {
                    "action": 'aws:runShellScript',
                    "name": 'EksctlAnywherePlugin_Install',
                    "inputs": {
                      "runCommand": [
                        'export EKSA_RELEASE="0.5.0" OS="$(uname -s | tr A-Z a-z)"',
                        'curl "https://anywhere-assets.eks.amazonaws.com/releases/eks-a/1/artifacts/eks-a/v${EKSA_RELEASE}/${OS}/eksctl-anywhere-v${EKSA_RELEASE}-${OS}-amd64.tar.gz" --silent --location | tar xz ./eksctl-anywhere',
                        'mv ./eksctl-anywhere /usr/local/bin/'
                      ]
                        }
                        }
                        ]
                        }
              
        )

        cfn_association = ssm.CfnAssociation(self, "MyCfnAssociation",
            name= cfn_document.ref ,
            targets=[ssm.CfnAssociation.TargetProperty(
            key="tag:Name",
            values=[envTagName]
            )]
        )


        CfnOutput(self, "InstanceID", value=instance.instance_id)







