import requests
import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime, timezone, timedelta

API_KEY = "HW52FN-38SNHM-5WKRHM-566K"  # Replace with your actual N2YO API key
BASE_URL = "https://api.n2yo.com/rest/v1/satellite"
OBSERVER_LAT = 35.0844  # Latitude for Albuquerque, New Mexico
OBSERVER_LNG = -106.6504  # Longitude for Albuquerque, New Mexico
OBSERVER_ALT = 1619  # Elevation in meters for Albuquerque, New Mexico

def utc_to_mst(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=-7)))

def get_visual_passes(sat_id, observer_lat, observer_lng, observer_alt, days):
    url = f"{BASE_URL}/visualpasses/{sat_id}/{observer_lat}/{observer_lng}/{observer_alt}/{days}/300/?apiKey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200 and response.json()['info']['passescount'] > 0:
        return response.json()['passes']
    return []

def main():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    norad_ids_str = simpledialog.askstring("Input", "Enter NORAD IDs, separated by commas:", parent=root)
    norad_ids = [id.strip() for id in norad_ids_str.split(',')] if norad_ids_str else []

    start_date_str = simpledialog.askstring("Input", "Enter the start date for observation (YYYY-MM-DD):", parent=root)
    days = simpledialog.askinteger("Input", "Enter the number of days for the observation period:", parent=root)

    if not start_date_str or not days or not norad_ids:
        messagebox.showinfo("Invalid Input", "Invalid input. Exiting.")
        return

    visible_satellites = []

    for sat_id in norad_ids:
        passes = get_visual_passes(sat_id, OBSERVER_LAT, OBSERVER_LNG, OBSERVER_ALT, days)
        if passes:
            visible_satellites.append((sat_id, passes))

    output_text = ""
    filename = "satellite_passes_record.txt"
    with open(filename, "a") as file:
        file.write(f"\n--- Satellite Passes Recorded at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} MST ---\n")
        for sat_id, passes in visible_satellites:
            file.write(f"\nSatellite NORAD ID: {sat_id}\n")
            for p in passes:
                pass_start_utc = datetime.utcfromtimestamp(p['startUTC'])
                pass_start_mst = utc_to_mst(pass_start_utc)
                file.write(f"  Visible pass starts at: {pass_start_mst.strftime('%Y-%m-%d %H:%M:%S')} MST\n")
        messagebox.showinfo("Output", f"Results appended to {filename}")

if __name__ == "__main__":
    main()
