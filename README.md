# aws_ami_cleanup

## Purpose
This script cleans up AMI images based on 
- region
- tag key/value pair 
- age of AMI created


## Scripts

`ami_cleanup.py` - for client machine usage

`lambda_ami_cleanup.py` - formatted for lambda usage; to be accompanied with **environment variables**

### Lambda Usage

key|value|Description
-|-|-|
TAG_KEY|name|Name of the tag key
TAG_VALUE|windows2016-base-|Name of the tag value. Script checks the value that begins with this string 
DAYS_OLD|14|Number of days since the creation of the AMI 
