import boto3
from botocore.exceptions import ClientError
import json
import time
import requests

# http://www.paramiko.org/ -  Help with ssh client and server
from paramiko import SSHClient, SFTPClient
import paramiko

## FUNCOES DE CRIACAOS

def criarChave():
    global ec2
    
    # Cria uma par de chaves
    key_pair = ec2.create_key_pair(KeyName='chaveScript')
    KeyPairOut = str(key_pair.key_material)

    # Cria um arquivo .pem com a chave
    with open('joaopmjm.pem','w') as file:
        file.write(KeyPairOut)

# Criar Grupo de seguranca

def criarSecurityGroup(name = 'default', portas = [22]):
    ec2 = boto3.client('ec2')
    rules = []
    for p in portas:
        rules.append({
            'IpProtocol': 'tcp',
            'FromPort': i,
                'ToPort': i,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]})

    response = ec2.describe_vpcs()
    vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')

    try:
        response = ec2.create_security_group(GroupName=name,
                                            VpcId=vpc_id,
                                            Description="Created by toranjascript")
        security_group_id = response['GroupId']
        print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))

        data = ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=rules)
        print('Ingress Successfully Set %s' % data)
    except ClientError as e:
        print("Error: ",e)
        return e
    return security_group_id

# Criando Load Balancer
# SG = SecurityGroup

def criarLoadBalancer(SG, nome ='joaopmjmLoadBalancer'):
    client = boto3.client('elb')
    deleteda = client.delete_load_balancer(
        LoadBalancerName=nome
    )   
    res = client.create_load_balancer(
        LoadBalancerName=nome,
        SecurityGroups=SG,
        Listeners=[
            {
                'Protocol': 'HTTP',
                'LoadBalancerPort': 80,
                'InstanceProtocol': 'HTTP',
                'InstancePort': 5000,
            }
        ],
        AvailabilityZones=[
            'us-east-1a',
            'us-east-1b',
            'us-east-1c',
            'us-east-1e',
            'us-east-1f',
            'us-east-1d'
        ],
        Tags=[
            {
                'Key':'Owner',
                'Value': 'Joaopmjm'
            },
        ]
    )
    return nome, res

# Criacao de AutoScale

def criarAutoScale(idInstancia, nome='joao', nomeLoad = 'joaopmjmLoadBalancer'):
    client = boto3.client('autoscaling')
    response = client.create_auto_scaling_group(
        AutoScalingGroupName=nome,
        InstanceId=idInstancia,
        MinSize=1,
        MaxSize=10,
        HealthCheckGracePeriod=300,
        LoadBalancerNames=[
            nomeLoad,
        ]
    )
    return response