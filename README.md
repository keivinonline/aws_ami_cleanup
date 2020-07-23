# aws_ami_cleanup

## Purpose
This script cleans up AMI images based on 
- region
- tag key/value pair 
- age of AMI created

It will
- skip AMIs that are associated to Auto-scaling Launch Configuration groups
- skip AMIs with inaccessible snapshots (e.g. AMI still in creation/pending state)

## Scripts

`ami_cleanup.py` - for client machine usage

`lambda_ami_cleanup.py` - formatted for lambda usage; to be accompanied with **environment variables**

### Lambda Environment Variables

key|value|Description
-|-|-|
TAG_KEY|name|Name of the tag key
TAG_VALUE|windows2016-base-|Name of the tag value. Script checks the value that begins with this string 
DAYS_OLD|14|Number of days since the creation of the AMI 
LAUNCH_CONFIG_CHECK|`true` / `false`| Whether to check the AMIs associated with Launch Configurations
DRY_RUN|`true` / `false`| Whether to run the script in test mode.<br> `True` - will procceed with test mode <br> `False` - **will DELETE AMIs and Snapshots !**

### Lambda IAM Role Policies Required
- `AWSLambdaBasicExecutionRole`
- `CustomAMIRole` with the following policy

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": "ec2:CreateTags",
            "Resource": "arn:aws:ec2:*::image/*"
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeImages",
                "ec2:DeregisterImage",
                "ec2:DeleteSnapshot",
                "ec2:DescribeSnapshotAttribute",
                "autoscaling:DescribeLaunchConfigurations",
                "ec2:DescribeImageAttribute",
                "ec2:DescribeSnapshots"
            ],
            "Resource": "*"
        }
    ]
}
```
## updates
1) 20200723 - 
- added `dry-run`
- added `failed_images` ,`failed_snapshots`, `failed_images_snapshot_access`
- replaced "description AMI" matching with "direct snapshot_id" reference via AMIs block device snapshotId reference
