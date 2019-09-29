# GDsaves-incremental-backup
# save GrimDawn Cloud Saves to the Cloud
# Bernhard Guenther <bernhard@guenther.pl>

import os
import json
import winreg 
import datetime
import zipfile
import lzma
import logging

# TODO  use windows %tempdir% to store zipfiles

settings = { 'version'    : '0.1',
             'gdsteamid' : '219990',
             'steampath'  : '',
             'steamuserid'  : '',
             'savefolder' : '',
             'remote_store' : 'awss3',
             'last_full_upload' : datetime.datetime.fromtimestamp(0).isoformat()
           }

GDzipfile = ''
GDzipfilepath = ''
archivedate = 0      
isFullBackup = False 
doIncremental = False
incrementalBackupIsNonEmpty = False
             
# we need to cache the save file folder and the upload credentials
def read_or_create_ini_file():
    global settings
    if not os.path.exists(os.path.expanduser('~/My Configs')):
        os.makedirs(os.path.expanduser('~/My Configs'))
    if not os.path.exists(os.path.expanduser('~/My Configs/GDsaves-incremental-backup.ini')):
        with open(os.path.expanduser('~/My Configs/GDsaves-incremental-backup.ini'), 'w') as settings_fp:
            json.dump(settings, settings_fp)
    else:
        with open(os.path.expanduser('~/My Configs/GDsaves-incremental-backup.ini'), 'r') as settings_fp:
            settings_from_file = json.load(settings_fp)
        # merge out settings with the default settings just in case we have missing entries
        settings = {**settings, **settings_from_file}
        
def save_init_file():
    global settings
    with open(os.path.expanduser('~/My Configs/GDsaves-incremental-backup.ini'), 'w') as settings_fp:
        json.dump(settings, settings_fp,indent=4)
    

def find_steam_userdir():
    global settings
    # example GD steam cloudsave dir C:\Program Files (x86)\Steam\userdata\<random_number>\219990\remote
    # <steampath>\userdata\<steamuserid>\<gdsteamid>\remote\save
    
    # find steam installation path from registry
    # HKEY_CURRENT_USER\Software\Valve\Steam
    reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Software\\Valve\\Steam')
    reg_value = winreg.QueryValueEx(reg_key, 'SteamPath')[0]
    settings['steampath'] = reg_value
    winreg.CloseKey(reg_key)
    # find steam user in registry
    reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Software\\Valve\\Steam\\Users')
    settings['steamuserid'] = winreg.EnumKey(reg_key, 0)
    winreg.CloseKey(reg_key)
    
    # now put together the Steam Grimdawn Cloudsave dir
    settings['savefolder'] = os.path.join(settings['steampath'],'userdata',settings['steamuserid'],settings['gdsteamid'],'remote','save')
    
def create_archive():
    global archivedate
    archivedate = datetime.datetime.now()
    timestamp = archivedate.strftime('%Y%m%d%H%M')
    archivename = "GrimDawnBackup-Steamuser%s-Fullbackup-Version%s.zip" % (settings['steamuserid'],timestamp)
    print('Creating archive ~/My Configs/'+archivename)
    gdzip = zipfile.ZipFile(os.path.expanduser('~/My Configs/'+archivename), 'w', zipfile.ZIP_LZMA)
    for root, dirs, files in os.walk(settings['savefolder']):
        for file in files:
            gdzip.write(os.path.join(root, file))
    gdzip.close()
    global GDzipfile
    GDzipfile = archivename
    global GDzipfilepath
    GDzipfilepath = os.path.expanduser('~/My Configs/'+archivename)
    global isFullBackup
    isFullBackup = True

# every incremental backup includes all files changed after last full backup (NOT last incremental backup)    
def create_incremental_archive():
    global settings
    last_full_archive = datetime.datetime.fromisoformat(settings['last_full_upload'])
    # if the last full archive is older than 10 days, lets create a full backup instead
    age = datetime.datetime.now() - last_full_archive
    print(repr(age))
    if age > datetime.timedelta(days=10):
        print("Last full backup is older than 10 days, so doing a full backup again")
        create_archive()
    else:
        print("Hell yeah")
        global archivedate
        archivedate = datetime.datetime.now()
        timestamp = archivedate.strftime('%Y%m%d%H%M')
        archivename = "GrimDawnBackup-Steamuser%s-Incrementalbackup-Version%s.zip" % (settings['steamuserid'],timestamp)
        print('Creating archive ~/My Configs/'+archivename)
        gdzip = zipfile.ZipFile(os.path.expanduser('~/My Configs/'+archivename), 'w', zipfile.ZIP_LZMA)
        number_of_newer_files = 0
        print("last full backup on %s" % last_full_archive.isoformat())
        for root, dirs, files in os.walk(settings['savefolder']):
            for file in files:
                filestat = os.stat(os.path.join(root, file))
                mtime = datetime.datetime.fromtimestamp(filestat.st_mtime)
                if mtime > last_full_archive:
                    gdzip.write(os.path.join(root, file))
                    number_of_newer_files += 1
        gdzip.close()
        global GDzipfile
        GDzipfile = archivename
        global GDzipfilepath
        GDzipfilepath = os.path.expanduser('~/My Configs/'+archivename)
        if number_of_newer_files > 0:
            global incrementalBackupIsNonEmpty
            incrementalBackupIsNonEmpty=True
            print("Found %i newer files. Adding to Archive." % number_of_newer_files)
        else:
            os.remove(GDzipfilepath)
        
    
def upload_archive():
    # TODO add methods
    # dropbox, remote_store="dropbox"
    # aws s3 bucket, remote_store="awss3"
    # google drive , remote_store="googledrive"
    # google cloud platform
    
    # for aws we need the user to do "pip install boto3"
    # also we need an access key and a bucket name + endpoint
    # http://boto3.readthedocs.io/en/latest/guide/s3-example-creating-buckets.html
    global settings
    global GDzipfile
    global GDzipfilepath
    global archivedate
    remote_store = settings['remote_store']
    
    if remote_store == 'awss3':
        # do a "pip install boto3" to install python aws sdk
        import boto3
        #import botocore
        from botocore.exceptions import ClientError
        # read credentials from GDsaves-incremental-backup-aws.ini in "My Configs" Folder
        if os.path.exists(os.path.expanduser('~/My Configs/GDsaves-incremental-backup-aws.ini')):
            access_key = ''
            access_secret = ''
            s3bucket = ''
            s3region = 'eu-central-1'
            with open(os.path.expanduser('~/My Configs/GDsaves-incremental-backup-aws.ini'), 'r') as awss3config_fp:
                for line in awss3config_fp:
                    (key, value) = line.replace(' ','').split('=')
                    if key == 'access_key': access_key = value.rstrip()
                    elif key == 'access_secret': access_secret = value.rstrip()
                    elif key == 's3bucket': s3bucket = value.rstrip()
                    elif key == 's3region': s3region = value.rstrip()
            awss3config_fp.close()
            #print('access_key="'+access_key+'"')
            #print('access_secret="'+access_secret+'"')
            session = boto3.session.Session()
            s3_client = session.client(
                service_name='s3',
                aws_access_key_id=access_key,
                aws_secret_access_key=access_secret,
                region_name=s3region,
                endpoint_url='https://s3.amazonaws.com',
                config=boto3.session.Config(signature_version='s3v4')
            )
            response = s3_client.list_buckets()
            buckets = [bucket['Name'] for bucket in response['Buckets']]
            if s3bucket not in buckets:
                print("S3 bucket '%s' does not exist in your account/region. Please create bucket first." % s3bucket)
            else:
                try:
                    print("Uploading zipfile to S3...")
                    response = s3_client.upload_file(GDzipfilepath, s3bucket,GDzipfile)
                except ClientError as e:
                    logging.error(e)
                else:
                    print("Upload Successful!")
                    # Now delete the local file again
                    os.remove(GDzipfilepath)
                    global isFullBackup
                    if isFullBackup:
                        settings['last_full_upload'] = archivedate.isoformat()
                    
        else:
            print('no aws config file found in ~/My Configs/GDsaves-incremental-backup-aws.ini, template created, please fill in details and restart again')
            with open(os.path.expanduser('~/My Configs/GDsaves-incremental-backup-aws.ini'), 'w') as awss3config_fp:
                awss3config_fp.write('access_key=\naccess_secret=\ns3bucket=\ns3region=eu-central-1\n')
            awss3config_fp.close()
            

if __name__ == '__main__':
    # read ini file first
    read_or_create_ini_file()
    #print(repr(settings))
    find_steam_userdir()
    #create_archive()
    create_incremental_archive() # this will also create a full archive if there is no older backup or the last full backup is older than 10 days
    if incrementalBackupIsNonEmpty or isFullBackup:
        if isFullBackup:
            print("Uploading Full Backup")
        else: 
            print("Uploading Incremental Backup")
        upload_archive()
    else:
        print("No newer files in savefolder found. Incremental Backup is empty. Not uploading.")
    save_init_file()
    