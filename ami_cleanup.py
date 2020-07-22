import boto3
import string
from datetime import datetime, timedelta
import re
'''
checking time for script to run
'''
startTime = datetime.now()
'''
variables
'''
var_region_name = "ap-southeast-1"
tag_key = "name"
tag_val = "windows2016-base-"
days_old = 14
launch_config_check = True

'''
Filter images based on "self" and tags defined
'''
ec2 = boto3.resource("ec2", region_name=var_region_name)
self_amis = ec2.images.filter(Owners=['self'])
filtered_amis = ec2.images.filter(
    Owners=['self'],
    Filters=[
        {
            'Name': 'tag:'+tag_key,
            'Values': [tag_val+'*']
        }
    ]
)
'''
Print self_amis
'''
print("List of self-owned AMI images are:")
for idx, image in enumerate(self_amis):
    print(f"[{idx}] {image.name}[{image.id}]")
print()
'''
Print filtered_amis
'''
print(f"List of matching AMI images based on tag '{tag_key}':'{tag_val}' are:")
for idx, image in enumerate(filtered_amis):
    print(f"[{idx}] {image.name}[{image.id}]")
print()

'''
check if age of AMI images is less than "days_old"
'''
purge_images = set()
print(
    f"List of matching AMI images which are also created less than '{days_old}' days are:")
for image in filtered_amis:
    created_at = datetime.strptime(
        image.creation_date,
        "%Y-%m-%dT%H:%M:%S.000Z",
    )
    if created_at > datetime.now() - timedelta(days_old):
        print(f"- {image.name}[{image.id}]")
        purge_images.add(image.id)
print()
'''
Get launch configuration associated AMIs
'''
if launch_config_check == True:
    client_as = boto3.client('autoscaling', region_name=var_region_name)
    launch_config_amis = client_as.describe_launch_configurations()[
        "LaunchConfigurations"]
    print("Getting list of AMIs used in Launch Configurations:")
    launch_config_ami_set = set()

    for idx, config in enumerate(launch_config_amis):
        config_name = config["LaunchConfigurationName"]
        config_image_id = config["ImageId"]
        print(f"[{idx}] [{config_image_id}] - used in '{config_name}'")
        launch_config_ami_set.add(config_image_id)

    print()
    '''
    Comparing sets and exclude AMIs used in Launch Configurations
    '''
    exclude_ami_set = purge_images.intersection(launch_config_ami_set)
    for image in exclude_ami_set:
        purge_images.remove(image)
    print("Final purge list:")
    for idx, image in enumerate(purge_images):
        print(f"[{idx}] {image}")
    print()

'''
Purge AMIs and snapshots
'''
print(f"Count of AMIs to purge: {len(purge_images)}")
if len(purge_images) > 0:
    '''
    Find matching associated snapshots
    '''
    myAccount = boto3.client('sts').get_caller_identity()['Account']
    client_ec2 = boto3.client("ec2", var_region_name)
    snapshots = client_ec2.describe_snapshots(
        OwnerIds=[myAccount])['Snapshots']

    purge_snapshots = set()
    for snapshot in snapshots:
        snapshot_id = snapshot["SnapshotId"]
        snapshot_description = snapshot["Description"]

        for image in purge_images:
            if re.search(image, snapshot_description):
                purge_snapshots.add(snapshot_id)
    '''
    Comparing snapshots used by Launch Configuration AMIs
    '''
    #TBC
    '''
    Purge AMIs
    '''
    for image in (image for image in filtered_amis if image.id in purge_images):
        print(f"Purging ==> {image.name}[{image.id}]")
        #image.deregister()  # uncomment this for actual deregistering
    print()
    '''
    Purge Snapshots
    '''
    print(f"Count of snapshots to purge: {len(purge_snapshots)}")
    for snapshot in purge_snapshots:
        print(f"Purging ==> {snapshot}")
        #client_ec2.delete_snapshot(SnapshotId=snapshot) # uncomment this for actual deletion
    print()
    print("Purge complete!")
else:
    print(f"No purging required !")
print()
'''
print time taken for script to run
'''
print(f"Time taken for purging - {datetime.now() - startTime}")
