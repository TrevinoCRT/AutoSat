import os
import dropbox
from datetime import datetime

def find_latest_observation_folder(base_folder):
    # List all subdirectories in the base folder
    subdirs = [os.path.join(base_folder, d) for d in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, d))]
    
    # Sort them by the modification time, latest first
    latest_folder = max(subdirs, key=os.path.getmtime, default=None)
    return latest_folder

def upload_to_dropbox(access_token, folder_path, dropbox_destination):
    dbx = dropbox.Dropbox(access_token)
    for filename in glob.glob(os.path.join(folder_path, '*.fit')):
        with open(filename, 'rb') as f:
            file_path_dropbox = os.path.join(dropbox_destination, os.path.basename(filename))
            try:
                dbx.files_upload(f.read(), file_path_dropbox)
                print(f"Uploaded {filename} to Dropbox")
            except Exception as e:
                print(f"Failed to upload {filename}: {e}")

def upload_latest_observation(access_token, base_folder, dropbox_destination):
    latest_folder = find_latest_observation_folder(base_folder)
    if latest_folder:
        print(f"Uploading files from {latest_folder} to Dropbox...")
        upload_folder_to_dropbox(access_token, latest_folder, dropbox_destination)
    else:
        print("No observation folders found.")

if __name__ == "__main__":
    ACCESS_TOKEN = ''  # Replace with your token
    BASE_FOLDER = 'C:/SatelliteData'
    DROPBOX_DESTINATION = '/Privateer'  # Replace with your Dropbox folder

    upload_latest_observation(ACCESS_TOKEN, BASE_FOLDER, DROPBOX_DESTINATION)
