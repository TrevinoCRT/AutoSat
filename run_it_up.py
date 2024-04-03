# -*- coding: utf-8 -*-
import requests
import tkinter as tk
from tkinter import messagebox, font, simpledialog, PhotoImage
from PIL import Image, ImageDraw, ImageFont
import subprocess
from datetime import datetime, timezone, timedelta
import threading
import json
import pytz
import os
import re
import sys
import traceback
import urllib.request
import time
print(sys.executable)

def show_button_info(info_text):
    info_popup = tk.Toplevel(app)
    info_popup.title("Information")
    info_popup.geometry("300x200")  # Adjust size as needed

    info_label = tk.Label(info_popup, text=info_text, wraplength=280)
    info_label.pack(pady=10, padx=10)

    close_button = tk.Button(info_popup, text="Close", command=info_popup.destroy)
    close_button.pack(pady=10)

def download_and_convert_image(url, jpg_filename, png_filename, size=(500, 500), observatory_coords=(305, 263), label_text="New Mexico Skies"):
    try:
        # Download the image
        print("Downloading image...")
        urllib.request.urlretrieve(url, jpg_filename)
        print("Image downloaded at:", os.path.abspath(jpg_filename))

        # Open the downloaded image
        with Image.open(jpg_filename) as img:
            # Resize the image
            img = img.resize(size, Image.Resampling.LANCZOS)  # Updated line
            
            # Draw a circle and label on the image
            draw = ImageDraw.Draw(img)
            draw.ellipse((observatory_coords[0]-4, observatory_coords[1]-4, observatory_coords[0]+4, observatory_coords[1]+4), fill='red')
            
            # Load a font
            font_path = "arial.ttf"  # Ensure this path is correct or accessible on your system
            try:
                font = ImageFont.truetype(font_path, 14)
            except IOError:
                print(f"Warning: Unable to load font '{font_path}'. Using default font.")
                font = ImageFont.load_default()
            
            # Draw text
            draw.text((314, 263), label_text, fill="white", font=font)
            
            # Save the modified image as PNG
            img.save(png_filename)
        
        print("Image processed. Final image at:", os.path.abspath(png_filename))
        return True
    except Exception as e:
        print(f"Error processing the image: {e}")
        return False


def update_image_label():
    jpg_filename = "weather.jpg"
    png_filename = "weather.png"
    image_url = "https://cdn.star.nesdis.noaa.gov/GOES16/ABI/SECTOR/sr/GEOCOLOR/600x600.jpg"

    if download_and_convert_image(image_url, jpg_filename, png_filename):
        if os.path.exists(png_filename):
            print("PNG file exists, updating label.")
            photo = tk.PhotoImage(file=png_filename)
            image_label.config(image=photo)
            image_label.image = photo  # keep a reference
        else:
            print("PNG file does not exist.")

    # Schedule the next update
    image_label.after(300000, update_image_label)  # Update every 5 minutes


def log_user_access(user_name):
    with open("access_log.txt", "a") as log_file:
        log_file.write(f"{user_name} accessed the application at {datetime.now()}\n")

def check_observatory_status():
    try:
        url = "https://nmskies.com/weather.php"
        response = requests.get(url)
        html_content = response.text

        # Use regular expression to find the image URL
        match = re.search(r'images/(daylight\.jpg|open\.jpg|closed\.jpg)\?', html_content)
        if match:
            img_file = match.group(1)
            if "daylight.jpg" in img_file:
                status = "Daylight (Closed)"
            elif "open.jpg" in img_file:
                status = "Open"
            elif "closed.jpg" in img_file:
                status = "Closed"
            else:
                status = "Unknown"
        else:
            status = "Status image not found"

        return status  # Returning the status string instead of displaying it
    except Exception as e:
        print(f"Failed to check observatory status: {e}")
        return "Error"  # Return an error status in case of an exception

def update_sun_times():
    try:
        lat, lng = 32.957313, -105.742485  # Coordinates for Cloudcroft, New Mexico
        today = datetime.now(pytz.timezone('America/Denver')).date()
        tomorrow = today + timedelta(days=1)

        # Fetch sunset time for today
        sunset_response = requests.get(f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lng}&date={today}&formatted=0")
        # Fetch sunrise time for tomorrow
        sunrise_response = requests.get(f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lng}&date={tomorrow}&formatted=0")

        if sunset_response.status_code != 200 or sunrise_response.status_code != 200:
            print(f"Failed to retrieve data from API. Status codes: {sunset_response.status_code}, {sunrise_response.status_code}")
            return None, None

        sunset_data = sunset_response.json()
        sunrise_data = sunrise_response.json()

        if 'results' not in sunset_data or 'sunset' not in sunset_data['results']:
            print("Malformed sunset API response: Missing 'results' or 'sunset' data.")
            return None, None

        if 'results' not in sunrise_data or 'sunrise' not in sunrise_data['results']:
            print("Malformed sunrise API response: Missing 'results' or 'sunrise' data.")
            return None, None

        sunset_utc = datetime.fromisoformat(sunset_data['results']['sunset'])
        sunrise_utc = datetime.fromisoformat(sunrise_data['results']['sunrise'])

        mountain_time = pytz.timezone('America/Denver')
        sunset_local = sunset_utc.replace(tzinfo=timezone.utc).astimezone(mountain_time)
        sunrise_local = sunrise_utc.replace(tzinfo=timezone.utc).astimezone(mountain_time)

        return sunrise_local, sunset_local
    except Exception as e:
        print(f"Error in update_sun_times: {e}")
        return None, None

# Function to determine the part of the day
def get_part_of_day(hour):
    return (
        "Good morning" if 5 <= hour <= 11
        else "Good afternoon" if 12 <= hour <= 17
        else "Good evening"
    )

def schedule_automation_function():
    # Prompt the user for the number of days
    num_days = simpledialog.askinteger("Input", "Enter number of days for observation cycle:", parent=app)
    if num_days is None or num_days <= 0:  # User cancelled or entered an invalid number
        return

    # Prompt the user for the daily start time
    daily_start_time_str = simpledialog.askstring("Input", "Enter daily start time (HH:MM):", parent=app)
    if not daily_start_time_str:  # User cancelled
        return
    
    try:
        daily_start_time = datetime.strptime(daily_start_time_str, "%H:%M").time()
    except ValueError:
        messagebox.showerror("Error", "Invalid time format. Please enter time in HH:MM format.")
        return

    # Schedule the observation cycle
    current_time = datetime.now()
    for day in range(num_days):
        cycle_datetime = current_time.replace(hour=daily_start_time.hour, minute=daily_start_time.minute, second=0, microsecond=0) + timedelta(days=day)

        if cycle_datetime < current_time:
            cycle_datetime += timedelta(days=1)

        wait_time = (cycle_datetime - current_time).total_seconds()
        threading.Timer(wait_time, automated_observation_cycle).start()

        # Print the scheduled time for the observation cycle
        print(f"Automated observation cycle scheduled for {cycle_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

    # Update the status label
    schedule_automation_status_label.config(text=f"Scheduled for {num_days} days")

def run_script(script_name, status_label, shutdown=False, args=None, completion_flag=None):
    def target():
        try:
            status_label.config(text="Status: Running")
            script_args = ['python', script_name] + (args if args is not None else [])
            if shutdown:
                script_args.append('shutdown')

            subprocess.run(script_args, check=True)
            status_label.config(text="Status: Finished")
            if completion_flag is not None:
                completion_flag.set()  # Set the flag when the script completes
        except Exception as e:
            error_message = f"Error running script: {e}\n{traceback.format_exc()}"
            print(error_message)  # Print the error message in the terminal
            status_label.config(text="Status: Error")

    threading.Thread(target=target).start()

def run_apiinteraction():
    run_script('api_interaction.py', tle_updater_status_label)

def open_tleplan():
    try:
        os.startfile('tleplan.txt')
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open tleplan.txt: {e}")

def run_automated2():
    run_script('automated2.py', automated2_status_label)
    
def automated_observation_cycle(num_days=None, daily_start_time=None):
    if num_days is None:
        num_days = 1  # Default number of days
    if daily_start_time is None:
        # Default start time to current time
        daily_start_time = datetime.now().time()  

    print("Automated observation cycle started.")
    for day in range(num_days):
        if not skip_scripts_var.get():
            # Run the TLE Updater script if the checkbox is not checked
            try:
                print("Running the TLE updater script.")
                subprocess.run(['python', 'api_interaction.py', '--non-interactive', '--days', '1', '--observation-window', '2'], check=True)
                tle_updater_status_label.config(text="TLE Updater: Finished")
            except subprocess.CalledProcessError as e:
                tle_updater_status_label.config(text=f"TLE Updater: Error ({e})")
                continue  # Skip the rest of the loop on error

        # Fetch Sunrise and Sunset Times
        print("Fetching sunrise and sunset times.")
        sunrise_time_next_day, sunset_time_today = update_sun_times()
        
        if sunrise_time_next_day and sunset_time_today:
            print(f"Sunset today and sunrise tomorrow times retrieved: {sunset_time_today}, {sunrise_time_next_day}")

            # Calculate Start and Shutdown Times
            print("Calculating start and shutdown times.")
            start_time = sunset_time_today + timedelta(minutes=5)
            shutdown_time = sunrise_time_next_day - timedelta(minutes=8)
            print(f"Start time: {start_time}, Shutdown time: {shutdown_time}")

            # Start Observation Function
            def start_observation():
                start_check_time = datetime.now()  # Record the time when checking starts
                while True:
                    status = check_observatory_status()
                    if status == "Open":
                        print("Observatory is open. Starting the observation script.")
                        break
                    elif (datetime.now() - start_check_time).total_seconds() > 5 * 3600:
                        print("Observatory not open for 5 hours. Initiating shutdown.")
                        initiate_shutdown()
                        exit()  # Quit the script
                    else:
                        print("Observatory is not open. Checking again in one minute.")
                        time.sleep(60)

                # Run Automated2.py Script
                run_script('automated2.py', automated2_status_label)

            # Initiate Shutdown Function
            def initiate_shutdown():
                print("Initiating the shutdown sequence.")
                run_script('automated2.py', automated2_status_label, shutdown=True)

            current_time = datetime.now(pytz.timezone('America/Denver'))

            # Check if it's already past the start time
            if current_time > start_time:
                print("Already past start time. Initiating observation immediately.")
                start_observation()  # Call the start observation function directly
            else:
                print("Scheduling the start of observation.")
                schedule_task(start_time, start_observation)  # Schedule as normal

            # Schedule shutdown as normal
            print("Scheduling the shutdown of observation.")
            schedule_task(shutdown_time, initiate_shutdown)

        else:
            print("Failed to retrieve sunrise and sunset times or data is incomplete.")
            # Implement your error handling or default setting here
            pass

        print("Automated observation cycle completed.")

def schedule_task(task_time, task_function):
    # Get the current time with the same timezone as task_time
    now = datetime.now(pytz.timezone('America/Denver'))
    wait_time = (task_time - now).total_seconds()
    if wait_time > 0:
        threading.Timer(wait_time, task_function).start()

def schedule_daily_cycle(num_days, daily_start_time):
    current_time = datetime.now()
    for day in range(num_days):
        # Calculate the date and time for the next cycle
        cycle_time = current_time.replace(hour=daily_start_time.hour, minute=daily_start_time.minute, second=0, microsecond=0) + timedelta(days=day)

        # If the cycle time is in the past, schedule for the next day
        if cycle_time < current_time:
            cycle_time += timedelta(days=1)

        wait_time = (cycle_time - current_time).total_seconds()
        threading.Timer(wait_time, automated_observation_cycle).start()
app = tk.Tk()
app.title("New Mexico Skies Command Center")

# Prompt for user's first name
user_name = simpledialog.askstring("Enter Name", "Please enter your first name:")

if user_name:
    # Fetch the current time in MTC timezone
    mtc_zone = pytz.timezone('America/Denver')
    mtc_time = datetime.now(mtc_zone)
    
    # Get the part of the day
    part_of_day = get_part_of_day(mtc_time.hour)

    personalized_title = f"{part_of_day} {user_name},\nWelcome to New Mexico Skies Command Center"
    app.title(personalized_title)
    log_user_access(user_name)
else:
    personalized_title = "Welcome to New Mexico Skies Command Center"
    app.title(personalized_title)

# Set the window size and make it not resizable
app.geometry("575x920")

# Modern NASA-style color scheme
background_color = "#D9D9D9"  # Light grey
button_color = "#404040"  # Dark grey
text_color = "#FFFFFF"  # White

# Define a new color for the 'Run all' button
run_all_button_color = "#00FF00"  # Green color

app.configure(bg=background_color)

# Modern font for the title and buttons
title_font = font.Font(family="Arial", size=18, weight="bold")
button_font = font.Font(family="Arial", size=12, weight="bold")

# Modify title label
title_label = tk.Label(app, text=personalized_title, bg=background_color, fg=text_color, font=title_font)
title_label.pack(pady=20)

button_style = {'font': button_font, 'bg': button_color, 'fg': text_color}

# Example for the TLE Updater button
tle_updater_info = (
    "TLE Updater Button:\n\n"
    "Description: The TLE (Two-Line Element) Updater fetches the visible overhead passes for selected satellites. "
    "It uses the N2YO API to process a list of NORAD satellite IDs and calculates their observation times. "
    "This script efficiently manages observation schedules by filtering out overlapping times and ensuring a minimum "
    "one-minute gap between consecutive observations.\n\n"
    "Usage:\n"
    "1. Update Existing NORAD IDs: Automatically updates observation times for previously saved satellite IDs, "
    "defaulting to a one-day-ahead observation period.\n"
    "2. Enter New NORAD IDs: Input a new list of NORAD IDs (comma-separated) and specify the number of days (1-10) "
    "for which you want to fetch observation periods.\n"
    "3. Enter the observation window for the satellite overpasses 'full' for the entire observation or ex. 2 minute "
    "observation window +/- 2 minutes from the midpoint of the observation.\n\n"
    "This tool is essential for planning and scheduling satellite tracking activities, ensuring a streamlined observation process."
)

tle_updater_frame = tk.Frame(app, bg=background_color)
tle_updater_frame.pack(pady=5)

button1 = tk.Button(tle_updater_frame, text="Run TLE Updater", command=lambda: run_apiinteraction(), **button_style)
button1.pack(side=tk.LEFT)

info_button1 = tk.Button(tle_updater_frame, text="?", command=lambda: show_button_info(tle_updater_info), font=button_font, bg=button_color, fg=text_color)
info_button1.pack(side=tk.LEFT, padx=5)

tle_updater_status_label = tk.Label(tle_updater_frame, text="Status: Idle", bg=background_color, fg=text_color, font=button_font)
tle_updater_status_label.pack(side=tk.LEFT)

see_schedule_button = tk.Button(app, text="See Observation Schedule", command=open_tleplan, **button_style)
see_schedule_button.pack(pady=10)

# Automated2.py Function Frame
automated2_info = (
    "Run Observation Button:\n\n"
    "Description: Triggers the central command script for telescope, dome, and tracking/imaging operations.\n\n"
    "Functionality:\n"
    "1. Initiates telescope and dome operations.\n"
    "2. Observation Execution: Executes observations listed in tleplan.txt through the run_observer script.\n"
    "3. Executes shutdown of equipment after run_observer concludes.\n\n"
    "Key for automated and efficient satellite observation."
)

automated2_frame = tk.Frame(app, bg=background_color)
automated2_frame.pack(pady=5)

button3 = tk.Button(automated2_frame, text="Run Observation(s)", command=lambda: run_automated2(), **button_style)
button3.pack(side=tk.LEFT)

info_button3 = tk.Button(automated2_frame, text="?", command=lambda: show_button_info(automated2_info), font=button_font, bg=button_color, fg=text_color)
info_button3.pack(side=tk.LEFT, padx=5)

automated2_status_label = tk.Label(automated2_frame, text="Status: Idle", bg=background_color, fg=text_color, font=button_font)
automated2_status_label.pack(side=tk.LEFT)

# Automated Observation Cycle Frame
automated_cycle_info = (
    "Automated Observation Cycle Button:\n\n"
    "Description: Initiates a sequential execution of three primary observation scripts.\n\n"
    "Functionality:\n"
    "1. TLE Updater: Begins with TLE updater using default NORAD IDs (in the Planewave, Scripts folder - STARLINK SATELLITES) for a one-day-ahead observation period.\n"
    "2. Observation Script Execution: Waits 10 minutes post-sunset to start the observation script.\n"
    "3. Observatory Status Check: Checks observatory status before initiating observations.\n"
    "4. Pre-Sunrise Shutdown: Sends shutdown request to the observation script 10 minutes before sunrise.\n\n"
    "Checkbox Option: Allows skipping TLE updater and filter via a checkbox below this button.\n\n"
    "Ensures a systematic and efficient observation process."
)

automated_cycle_frame = tk.Frame(app, bg=background_color)
automated_cycle_frame.pack(pady=5)

automated_cycle_button = tk.Button(automated_cycle_frame, text="Start Automated Cycle", command=automated_observation_cycle, font=button_font, bg="#00FF00", fg=text_color)
automated_cycle_button.pack(side=tk.LEFT)

info_button_cycle = tk.Button(automated_cycle_frame, text="?", command=lambda: show_button_info(automated_cycle_info), font=button_font, bg=button_color, fg=text_color)
info_button_cycle.pack(side=tk.LEFT, padx=5)

automated_cycle_status_label = tk.Label(automated_cycle_frame, text="Status: Idle", bg=background_color, fg=text_color, font=button_font)
automated_cycle_status_label.pack(side=tk.LEFT)

def update_checkbox_label():
    if skip_scripts_var.get():
        checkbox_status_label.config(text="Skipping TLE Updater")
    else:
        checkbox_status_label.config(text="Including TLE Updater")

skip_scripts_var = tk.BooleanVar(value=False)
skip_scripts_checkbox = tk.Checkbutton(app, text="Skip TLE Updater", variable=skip_scripts_var, onvalue=True, offvalue=False, bg=background_color, fg=text_color, font=button_font, command=update_checkbox_label)
skip_scripts_checkbox.pack(pady=10)

checkbox_status_label = tk.Label(app, text="Including TLE Updater", bg=background_color, fg=text_color, font=button_font)
checkbox_status_label.pack(pady=5)

def on_schedule_cycle_button_click():
    num_days = ask_user_for_number_of_days()
    daily_start_time = ask_user_for_daily_start_time()

    schedule_daily_cycle(num_days, daily_start_time)


schedule_automation_info = (
    "Schedule Automated Observation Cycle Button:\n\n"
    "Description: Allows scheduling of automated observation cycles over multiple days at specified times.\n\n"
    "Functionality:\n"
    "1. User defines the number of days for the observation cycle.\n"
    "2. User sets a daily start time for the cycle.\n"
    "3. The script automatically initiates the observation cycle at the specified time each day.\n"
    "4. Observations start 10 minutes before sunset and end 15 minutes before the next day's sunrise.\n\n"
    "Provides flexibility for extended and scheduled astronomical observations."
)
# Schedule Automated Observation Cycle Frame
schedule_automation_frame = tk.Frame(app, bg=background_color)
schedule_automation_frame.pack(pady=5)

schedule_automation_button = tk.Button(schedule_automation_frame, text="Schedule Automated Observation Cycle", command=lambda: schedule_automation_function(), **button_style)
schedule_automation_button.pack(side=tk.LEFT)

info_button_schedule_automation = tk.Button(schedule_automation_frame, text="?", command=lambda: show_button_info(schedule_automation_info), font=button_font, bg=button_color, fg=text_color)
info_button_schedule_automation.pack(side=tk.LEFT, padx=5)

schedule_automation_status_label = tk.Label(schedule_automation_frame, text="Status: Idle", bg=background_color, fg=text_color, font=button_font)
schedule_automation_status_label.pack(side=tk.LEFT)

image_label = tk.Label(app)
image_label.pack(pady=5)

update_image_label()

app.mainloop()
