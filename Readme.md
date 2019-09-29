GDsaves-incremental-backup

This Python script will create incremental backups of your GrimDawn Cloud Saves and upload them to AWS S3.


Prerequisites:

- Python3.7
- boto3  - Do a "pip install boto3" in your python Folder
- S3 Bucket for the files (script does not create the bucket)

The First run of GDsaves-incremental-backup.py  will create ini files in %userfolder%\My Configs

You can check the GDsaves-incremental-backup.ini for the Steam Cloudsave Folder for Grimdawn (the script should find that folder itself). It will create a "template" for the AWS Credentials (GDsaves-incremental-backup-aws.ini)

But you definitely have to add your AWS Credentials and the Name of the S3 Bucket to GDsaves-incremental-backup-aws.ini

At first run it will zip the whole save folder and upload it to S3. It will save the timestamp of the file after successful upload to the ini file.
Successive runs of the script will add only newer files from the save folder to the zipfiles for upload.
After 10 Days it will create a new full backup though.

If you want to tweak this you can change the number in line 95.

This is the first rough version of this script. 

I do not garantee the workings of this script and take no responsibility for any lost files. Use at your own risk.
