import os
import boto3
import string
from datetime import datetime, timedelta 
import re

def lambda_handler(event, context):
    '''
    variables
    '''
    var_region_name = os.environ['AWS_REGION']
    tag_key = os.environ['TAG_KEY']
    tag_val = os.environ['TAG_VALUE']
    days_old = int(os.environ['DAYS_OLD'])

    '''
    initiate boto3 package
    '''
    ec2 = boto3.resource("ec2", region_name=var_region_name) 

    '''
    Filter images based on "self" and tags defined
    '''
    self_images = ec2.images.filter(Owners=['self'])
    filtered_images = ec2.images.filter(
        Owners=['self'],
        Filters=[
            {
                'Name': 'tag:'+tag_key,
                'Values': [tag_val+'*']
                }
        ]
    )
    '''
    Print self_images
    '''
    print("List of self-owned AMI images are:")
    for idx,image in enumerate(self_images):
        print(f"[{idx}] {image.name}-{image.id}")
    print()
    '''
    Print filtered_images
    '''
    print(f"List of matching AMI images based on tag '{tag_key}':'{tag_val}' are:")
    for idx,image in enumerate(filtered_images):
        print(f"[{idx}] {image.name}-{image.id}")
    print()

    '''
    check if age of AMI images is less than "days_old"
    '''
    purge_images = set()

    for image in filtered_images:
        created_at = datetime.strptime(
            image.creation_date,
            "%Y-%m-%dT%H:%M:%S.000Z",
        )
        compare_date = datetime.now() - timedelta(days_old)
        if created_at > datetime.now() - timedelta(days_old):
            print(f"Appending to purge_images set: {image.name}[{image.id}]")
            purge_images.add(image.id)
    print()

    '''
    Purge AMIs and snapshots
    '''
    print(f"Count of AMIs to purge: {len(purge_images)}")
    if len(purge_images) > 0:
        for image in (image for image in filtered_images if image.id in purge_images):
            print(f"Purging ==> {image.name}[{image.id}]")
            #image.deregister()  # uncomment this for actual deregistering
        print()
        '''
        Find matching associated snapshots
        '''
        myAccount = boto3.client('sts').get_caller_identity()['Account']
        client = boto3.client("ec2",var_region_name)
        snapshots= client.describe_snapshots(OwnerIds=[myAccount])['Snapshots']

        purge_snapshots = set()
        for snapshot in snapshots:
            snapshot_id = snapshot["SnapshotId"]
            snapshot_vol_size = snapshot["VolumeSize"]
            snapshot_description = snapshot["Description"]
            
            for image in purge_images:
                if re.search(image,snapshot_description):
                    print(f"Appending to purge_snapshots set: {snapshot_id}")
                    purge_snapshots.add(snapshot_id)
        print()

        print(f"Count of snapshots to purge: {len(purge_snapshots)}")
        for snapshot in purge_snapshots:
            print(f"Purging ==> {snapshot}")
            #client.delete_snapshot(SnapshotId=snapshot) # uncomment this for actual deletion
        print()
        print("Purge complete!")
    else:
        print(f"No purging required !")
    print()