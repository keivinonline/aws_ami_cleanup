import boto3
import string
from datetime import datetime, timedelta 

'''
variables
'''
var_region_name = "ap-southeast-1"
tag_key = "name"
tag_val = "windows2016-base-"
days_old = 14

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
Purge AMIs
'''
print(f"Count of AMIs to purge: {len(purge_images)}")
if len(purge_images) > 0:
    for image in (image for image in filtered_images if image.id in purge_images):
        print(f"Purging: {image.name}[{image.id}]")
        #image.deregister()  # uncomment this for actual deregistering
        print("Purge complete!")
else:
    print(f"No purging required !")
print()