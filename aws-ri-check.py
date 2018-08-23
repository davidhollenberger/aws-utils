from collections import defaultdict
import argparse
import boto3
import datetime
import sys
import pytz


parser = argparse.ArgumentParser(
    description="Shows summary about 'Reserved' and 'On-demand' ec2 instances")

parser.add_argument("-r", "--region", type=str, default="us-east-1",
                    help="AWS Region name. Default is 'us-east-1'")

parser.add_argument("-f", "--forecast", type=int, default=30,
                    help="Forecast RI coverage this many days from now. "
                         "Default is '30 days'")

args = parser.parse_args()

timezone = pytz.timezone("UTC")
forecast_date = timezone.localize(datetime.datetime.utcnow() + datetime.timedelta(days=args.forecast))


filters = [{'Name': 'instance-state-name', 'Values': ['running']}]

ec2_resource = boto3.resource('ec2', region_name='us-east-1')

instances = ec2_resource.instances.filter(
    Filters=filters
)

# RI Normalization Factor
# from https://aws.amazon.com/blogs/aws/new-instance-size-flexibility-for-ec2-reserved-instances/
ri_normalization_factor = {
'nano':	0.25,
'micro': 0.5,
'small': 1,
'medium': 2,
'large': 4,
'xlarge': 8,
'2xlarge': 16,
'4xlarge': 32,
'8xlarge': 64,
'10xlarge': 80,
'16xlarge': 128,
'32xlarge': 256,
}

instance_types = {
'c1': ['medium', 'xlarge'],
'c3': ['2xlarge', '4xlarge', '8xlarge', 'large', 'xlarge'],
'c4': ['2xlarge', '4xlarge', '8xlarge', 'large', 'xlarge'],
'c5': ['18xlarge', '2xlarge', '4xlarge', '9xlarge', 'large', 'xlarge'],
'c5d': ['18xlarge', '2xlarge', '4xlarge', '9xlarge', 'large', 'xlarge'],
'cc2': ['8xlarge'],
'cr1': ['8xlarge'],
'd2': ['2xlarge', '4xlarge', '8xlarge', 'xlarge'],
'f1': ['16xlarge', '2xlarge'],
'g2': ['2xlarge', '8xlarge'],
'g3': ['16xlarge', '4xlarge', '8xlarge'],
'h1': ['16xlarge', '2xlarge', '4xlarge', '8xlarge'],
'hs1': ['8xlarge'],
'i2': ['2xlarge', '4xlarge', '8xlarge', 'xlarge'],
'i3': ['16xlarge', '2xlarge', '4xlarge', '8xlarge', 'large', 'metal', 'xlarge'],
'm1': ['large', 'medium', 'small', 'xlarge'],
'm2': ['2xlarge', '4xlarge', 'xlarge'],
'm3': ['2xlarge', 'large', 'medium', 'xlarge'],
'm4': ['10xlarge', '16xlarge', '2xlarge', '4xlarge', 'large', 'xlarge'],
'm5': ['12xlarge', '24xlarge', '2xlarge', '4xlarge', 'large', 'xlarge'],
'm5d': ['12xlarge', '24xlarge', '2xlarge', '4xlarge', 'large', 'xlarge'],
'p2': ['16xlarge', '8xlarge', 'xlarge'],
'p3': ['16xlarge', '2xlarge', '8xlarge'],
'r3': ['2xlarge', '4xlarge', '8xlarge', 'large', 'xlarge'],
'r4': ['16xlarge', '2xlarge', '4xlarge', '8xlarge', 'large', 'xlarge'],
't1': ['micro'],
't2': ['2xlarge', 'large', 'medium', 'micro', 'nano', 'small', 'xlarge'],
'x1': ['16xlarge', '32xlarge'],
'x1e': ['16xlarge', '2xlarge', '32xlarge', '4xlarge', '8xlarge', 'xlarge']
}

# dictionary to add total RI normalization of running ec2 instances
od_total = {}

running_instances = {}

# template = "{0:70}| {1:5}| {2:5}| {3:5}"
# print template.format("Name", "Instance Family", "Instance Size", "Normalization Factor")

for i in instances:
    for tag in i.tags:
        if 'env'in tag['Key']:
            environment = tag['Value']
        if 'Name' in tag['Key']:
            name = tag['Value']
    instance_type = i.instance_type.split(".")
    family = instance_type[0]
    size = instance_type[1]


    if family in od_total:
        od_total[family] += ri_normalization_factor[size]
    else:
        od_total[family] = ri_normalization_factor[size]

    if i.instance_type in running_instances:
        running_instances[i.instance_type]['count'] += 1
        running_instances[i.instance_type]['instances'] += [name]
    else:
        new_instance = {'count':1, 'instances':name}
        running_instances[i.instance_type] = {}
        running_instances[i.instance_type]['count'] = 1
        running_instances[i.instance_type]['instances'] = [name]

    # print template.format(name, family, size, ri_normalization_factor[size])


print(od_total)


for key, value in running_instances.items():
    print(key, value['count'])

# Retrieve reserved instances
ec2_client = boto3.client('ec2')
filters = [{'Name': 'state', 'Values': ['active']}]
reservations = ec2_client.describe_reserved_instances(
    Filters=filters
)

ri_total = defaultdict(int)

reserved_instances = {}

print("Reserved Instances on ", forecast_date)

for ri in reservations['ReservedInstances']:
    if ri['End'] > forecast_date:
        instance_type = ri['InstanceType'].split(".")
        family = instance_type[0]
        size = instance_type[1]
        print(family, size, ri['InstanceCount'], ri['InstanceCount'] * ri_normalization_factor[size])

        ri_total[family] += ri['InstanceCount'] * ri_normalization_factor[size]


print(ri_total)


# RI Coverage
print('')
for key,value in od_total.items():
    print("------------")
    print(key)
    print("------------")

    if key in ri_total:
        ricoverage = ri_total[key] / od_total[key]
        print("RI Coverage: {:.1%}".format(ricoverage))
        if ri_total[key] > od_total[key]:
            print(ri_total[key] - od_total[key]," unused RI normalized credits")
        elif ri_total[key] < od_total[key]:
            print(od_total[key]-ri_total[key]," RI normalized credits needed")

            #calculate what needs to be purchased to reach 80% RI coverage
            ritarget = .8 * od_total[key] - ri_total[key]
            print("80% target: ", .8 * od_total[key] - ri_total[key])

            # for k, v in sorted(ri_normalization_factor.items(), key=lambda (k,v): (v,k), reverse=True):
            #     if v <= ritarget:
            #         if k in instance_types[key]:
            #             numinstances = ritarget // v
            #             ritarget -= v * numinstances
            #             print "Purchase ",numinstances," x ",key, ".",k, "(",v*numinstances," credits)"


        else:
            print("0 RI normalized credits needed")
    else:
        ricoverage = 0
        print("No reserved instances.  Needs ",od_total[key],"RI normalized credits")
        print("80% target: ", .8 * od_total[key] - ri_total[key])


    print("")

# # Report
# print("Reserved instances:")
# for k, v in sorted(six.items(reserved_instances), key=lambda x: x[0]):
#     print("\t(%s)\t%12s\t%s\t%s" % ((v,) + k))
# print("")
#
#
# print("Expiring soon (less than %sd) reserved instances:" % args.warn_time)
# for k, v in sorted(six.items(soon_expire_ri), key=lambda x: x[1][:2]):
#     (platform, instance_type, region, expire_date) = v
#     expire_date = expire_date.strftime('%Y-%m-%d')
#     print("\t%s\t%12s\t%s\t%s\t%s" % (k, platform, instance_type, region,
#                                     expire_date))
# if not soon_expire_ri:
#    print("\tNone")
# print("")
#
#
# print("Running on-demand instances:   %s" % sum(running_instances.values()))
# print("Reserved instances:            %s" % sum(reserved_instances.values()))
# print("")
