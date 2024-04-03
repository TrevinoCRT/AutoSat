import time
import os
from datetime import datetime, timedelta
import win32com.client
import logging
import traceback
from pwi4_client import PWI4
import pytz

ddw = win32com.client.Dispatch("TIDigitalDomeWorks.DomeControl")

logging.basicConfig(filename='telescope_automation_log.txt', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


class TelescopeController:
    # Assuming PWI4 class is already defined in the pwi4_client module
    def __init__(self):
        self.pwi4 = PWI4()

    def slew_to_coordinates(self, ra_hours, dec_degs):
        # Using mount_goto_ra_dec_j2000 to slew the telescope
        return self.pwi4.mount_goto_ra_dec_j2000(ra_hours, dec_degs)

def startup_pwi4():
    try:
        print("Initializing PWI4...")
        pwi4 = PWI4()
        logging.info("PWI4 instance created.")

        def connect_to_mount():
            print("Connecting to the mount...")
            pwi4.mount_connect()
            while not pwi4.status().mount.is_connected:
                time.sleep(1)
            logging.info("Mount connected.")
            print("Mount connected.")

        def enable_motors():
            print("Enabling motors...")
            pwi4.mount_enable(0)  # Enable axis 0
            pwi4.mount_enable(1)  # Enable axis 1
            logging.info("Motors enabled.")
            print("Motors enabled.")

        def find_home():
            print("Finding home position...")
            pwi4.mount_find_home()
            last_axis0_pos_degs = -99999
            last_axis1_pos_degs = -99999
            while True:
                status = pwi4.status()
                delta_axis0_pos_degs = abs(status.mount.axis0.position_degs - last_axis0_pos_degs)
                delta_axis1_pos_degs = abs(status.mount.axis1.position_degs - last_axis1_pos_degs)
                if delta_axis0_pos_degs < 0.001 and delta_axis1_pos_degs < 0.001:
                    break
                last_axis0_pos_degs = status.mount.axis0.position_degs
                last_axis1_pos_degs = status.mount.axis1.position_degs
                time.sleep(1)
            logging.info("Home position found.")
            print("Home position found.")

        connect_to_mount()
        enable_motors()
        find_home()
        return pwi4

    except Exception as e:
        logging.error(f"Error in startup_pwi4: {e}")
        traceback.print_exc()
        print(f"Error occurred in startup_pwi4: {e}")

#Function to Control Dome via ASCOM
def control_ddw(ddw, action, azimuth=None):
    try:
        # Check if the dome is busy
        while ddw.statIsBusy():
            time.sleep(1)

        # Check if the dome system is online
        if not ddw.statIsOnline():
            raise Exception("DDW is not running.")

        if action == "open_shutter":
            ddw.actOpenShutter()
            time.sleep(5)  # Adjust sleep time as needed
            if not ddw.statIsShutterOpen():  # Check if the shutter is open
                raise Exception("Failed to open dome shutter.")
            print("Dome shutter opened.")

        elif action == "close_shutter":
            ddw.actCloseShutter()
            time.sleep(5)  # Adjust sleep time as needed
            print("Dome shutter closed.")

        elif action == "slave_to_telescope":
            ddw.optSlaveMode = True
            print("Dome slaving to telescope enabled.")

    except Exception as e:
        logging.error(f"Error in control_ddw: {e}")
        traceback.print_exc()
        raise  # Re-raise the exception to be caught by the calling function

def operate_camera(action, cam, image_dir, image_count):
    if action == 'open':
        cam.Expose(EXPOSURE_LENGTH_SEC, 1)  # Start exposure
    elif action == 'close':
        while not cam.ImageReady:
            time.sleep(0.1)
        filename = f"{image_count:04d}.fits"  # Modify as needed
        full_file_path = os.path.join(image_dir, filename)
        cam.SaveImage(full_file_path)

def schedule_observations(asteroid_data, telescope_controller):
    cam = Dispatch("MaxIm.CCDCamera")
    cam.LinkEnabled = True
    cam.DisableAutoShutdown = True
    image_dir = 'path/to/image_directory'  # Specify the directory for saving images
    image_count = 1  # Initialize image count

    for observation in asteroid_data:
        current_time = datetime.now(pytz.timezone('MST')).strftime('%Y-%m-%d %H:%M')
        if current_time == observation['observation_time']:
            ra_hours = float(observation['RA']) / 15  # Convert RA from degrees to hours
            dec_degs = float(observation['DEC'])
            telescope_controller.slew_to_coordinates(ra_hours, dec_degs)
            operate_camera('open', cam, image_dir, image_count)
            operate_camera('close', cam, image_dir, image_count)
            image_count += 1

# Function to read asteroid data from file
def read_asteroid_data(filename):
    asteroid_data = []
    with open(filename, 'r') as file:
        for line in file:
            parts = line.split()
            asteroid_data.append({'asteroid_id': parts[0], 'observation_time': parts[1] + ' ' + parts[2], 'RA': parts[4], 'DEC': parts[6]})
    return asteroid_data


def main():
    global dome_open
    try:
        print("Starting observation script...")
        logging.info("Script started")
        pwi4 = startup_pwi4()

        # Check if the dome door and shutter are open
        dome_door_open = ddw.statIsDomeDoorOpen()
        shutter_open = ddw.statIsShutterOpen()
        if not dome_door_open or not shutter_open:
            print("Performing dome operations...")
            control_ddw(ddw, "open_shutter")
            control_ddw(ddw, "slave_to_telescope")
            dome_open = True
            time.sleep(180)  # Adjust the time as needed (180 seconds = 3 minutes)
        else:
            print("Dome already open, skipping wait time.")

        telescope_controller = TelescopeController()
        asteroid_data = read_asteroid_data('asteroid_observations.txt')
        schedule_observations(asteroid_data, telescope_controller)

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("Telescope automation script initiated.")
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
