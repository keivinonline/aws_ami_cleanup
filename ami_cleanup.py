import boto3
import string
from datetime import datetime, timedelta

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
dry_run = True

'''
Filter images based on "self" and tags defined
'''
ec2 = boto3.resource("ec2", region_name=var_region_name)
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
purge_snapshots = set()
failed_images = set()
failed_images_snapshot_access = set()
failed_snapshots = set()
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

    print()

'''
Purge AMIs and snapshots
'''

client_ec2 = boto3.client("ec2", var_region_name)

if len(purge_images) > 0:
    '''
    Get AMIs and corresponding snapshots
    '''
    final_purge = ec2.images.filter(
        Owners=['self'], ImageIds=list(purge_images))

    print("Final purge list - AMI to Snapshots mapping:")
    for idx, image in enumerate(final_purge):
        for idx2, block_device_mappings in enumerate(image.block_device_mappings):
            try:
                snapshot_id = block_device_mappings['Ebs']['SnapshotId']
                print(f"[{idx}][{idx2}] {image.name}[{image.id}] - {snapshot_id}")
                purge_snapshots.add(snapshot_id)
            except Exception as e:
                failed_images.add(image.id)           
                failed_images_snapshot_access.add(image.id)
    print()
    '''
    Remove failed images from purge_images set
    '''
    purge_images.difference_update(failed_images)
    '''
    Purge AMIs
    '''
    print(f"Count of AMIs to purge: {len(purge_images)}")
    for image in purge_images:
        try:
            print(f"Purging Image  ==> {image}")
            client_ec2.deregister_image(
                ImageId=image,
                DryRun=bool(dry_run) # True|False
                )
        except Exception as e:
            if 'DryRunOperation' in str(e):
                print(f"[DryRun] Purging Image succeeded ==> {image}")
                print()
            else:
                print(f"Purging Image Failed ==> {image}")
                failed_images.add(image)
                print(f"{e}")
    print()
    '''
    Purge Snapshots
    '''
    print(f"Count of snapshots to purge: {len(purge_snapshots)}")
    for snapshot in purge_snapshots:
        try:
            print(f"Purging Snapshot ==> {snapshot}")
            client_ec2.delete_snapshot(
                SnapshotId=snapshot,
                DryRun=bool(dry_run) # True|False
                ) 
        except Exception as e:
            if 'DryRunOperation' in str(e):
                print(f"[DryRun] Purging Snapshot succeeded ==> {image}")
                print()
            else:
                print(f"Purging Snapshot Failed ==> {snapshot}")
                failed_snapshots.add(snapshot)
                print(f"{e}")

    if len(failed_images):
        print()
        print(f"Unable to purge images for:")
        for idx,image in enumerate(failed_images):
            print(f"[{idx}] {image}")
    if len(failed_images_snapshot_access):
        print()
        print(f"Unable to fetch snapshot_id for:")
        for idx,image in enumerate(failed_images_snapshot_access):
            print(f"[{idx}] {image}")
    if len(failed_snapshots):
        print()
        print(f"Unable to purge snapshot_id:")
        for idx,snapshots in enumerate(failed_snapshots):
            print(f"[{idx}] {snapshots}")
    print()
    print("Purge complete!")
else:
    print()
    print(f"No purging required !")
print()
'''
print time taken for script to run
'''
print(f"Time taken for purging - {datetime.now() - startTime}")
