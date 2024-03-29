from collections import defaultdict
import argparse
import boto3
import datetime
import sys
import jinja2
from shutil import copy2
import os
import uuid



parser = argparse.ArgumentParser(
    description="Generate iTerm Profiles for EC2 Instances")

parser.add_argument("-r", "--region", type=str, action='append')

parser.add_argument("-u", "--user", type=str, default="",
                    help="SSH User")

parser.add_argument("-p", '--profile', action='append')

args = parser.parse_args()
ssh_user = args.user


filters = [{'Name': 'instance-state-name', 'Values': ['running']},
            {'Name':'tag:env', 'Values':['lab','stage','prod']}]

for profile_name in args.profile:
    for region in args.region:


        session = boto3.session.Session(profile_name=profile_name, region_name=region)

        # for profile in boto3.session.Session().available_profiles:
        #     print('Available Profiles: '+profile)

        if profile_name in boto3.session.Session().available_profiles:
            print('Gathering ec2 facts for '+profile_name+' ('+region+')')

            ec2_resource = session.resource('ec2', region_name=region)

            instances = ec2_resource.instances.filter(Filters=filters)
            for instance in instances:
                print (instance.id, instance.instance_type, region)

            iterm_instances = {}

            for i in instances:
                iterm_instances[i.id] = {}
                iterm_instances[i.id]['instance_type'] = i.instance_type
                iterm_instances[i.id]['private_ip_address'] = i.private_ip_address
                iterm_instances[i.id]['guid'] = uuid.uuid4()

                for tag in i.tags:
                    if 'env'in tag['Key']:
                        environment = tag['Value']
                        if environment not in ['lab','prod']:
                            environment = 'nonprod'
                        iterm_instances[i.id]['environment'] = environment

                    if 'Name' in tag['Key']:
                        name = tag['Value']
                        #Build full postgres name from other tags
                        if name.startswith('pg-'):
                            pg_cluster = None
                            role = None
                            for t in i.tags:
                                if 'pg_cluster'in t['Key']:
                                    pg_cluster = t['Value']
                                if 'role' in t['Key']:
                                    role = t['Value']

                            if pg_cluster is not None:
                                name += '-'+pg_cluster
                            if role is not None:
                                name += '-'+role
                        iterm_instances[i.id]['name'] = name


            # for key, value in iterm_instances.items():
            #   print('ec2_id: '+key)
            #   print('  name: '+value['name'])
            #   print('  env:  '+value['environment'])
            #   print('  ip: '+value['private_ip_address'])

                # print(i.id, i.instance_type, i.private_ip_address, i.key_name, environment, name)

            # Template iTerm Dynamic Profile
            templateLoader = jinja2.FileSystemLoader(searchpath="./templates")
            templateEnv = jinja2.Environment(loader=templateLoader)
            TEMPLATE_FILE = "dynamic_profile.j2"
            template = templateEnv.get_template(TEMPLATE_FILE)
            dest_path = os.path.expanduser('~/Library/Application Support/iTerm2/DynamicProfiles/')
            template.stream(iterm_instances=iterm_instances, ssh_user=ssh_user, region=session.region_name, profile=session.profile_name).dump(dest_path+'aws_'+profile_name+'_'+session.region_name)


        # outputText = template.render(iterm_instances=iterm_instances, ssh_user=ssh_user, region=region)
        #print(outputText)
