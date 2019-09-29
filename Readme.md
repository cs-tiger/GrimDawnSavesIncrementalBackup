GDsaves-incremental-backup

This Python script will create incremental backups of your GrimDawn Cloud Saves and upload them to AWS S3.


Prerequisites:

Python3.7
boto3  - Do a "pip install boto3" in your python Folder
S3 Bucket for the files (script does not create the bucket)

The First run of GDsaves-incremental-backup.py  will create ini files in %userfolder%\My Configs
You can check the GDsaves-incremental-backup.ini for the Steam Cloudsave Folder for Grimdawn (the script should find that folder itself).
But you definitely have to add your AWS Credentials and the Name of the S3 Bucket to GDsaves-incremental-backup-aws.ini