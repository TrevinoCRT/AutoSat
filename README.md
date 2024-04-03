# New Mexico Skies Command Center

This repository contains Python scripts for automating and managing satellite observations at the New Mexico Skies observatory.

## Table of Contents
- [Introduction](#introduction)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [API Key Setup](#api-key-setup)
- [Usage](#usage)
  - [Run_it_up.py GUI](#run_it_uppy-gui)
  - [API Interaction Script (api_interaction.py)](#api-interaction-script-api_interactionpy)
  - [Other Scripts](#other-scripts)
- [Contributing](#contributing)
- [License](#license)

## Introduction

The New Mexico Skies Command Center provides a user-friendly interface and automation capabilities for satellite observation tasks. The main script, `run_it_up.py`, offers a GUI with various options to streamline the observation process.

## Getting Started

### Prerequisites

- Python 3.x (https://www.python.org/)
- Required Python libraries:
  - requests
  - tkinter
  - PIL
  - subprocess
  - datetime
  - pytz
  - os
  - re
  - sys
  - traceback
  - urllib.request
  - time
  - pythoncom
  - pwi4_client
  - win32com.client
  - aiohttp
  - asyncio
  - dotenv

### Installation

1. Clone or download this repository.
2. Install the required Python libraries using `pip install <library_name>`.

### API Key Setup

1. Create a `.env` file in the root directory of the repository.
2. Add the following line to the `.env` file, replacing `<your_api_key>` with your actual N2YO API key: `API_KEY=<your_api_key>`
3. Use code with caution. In `api_interaction.py`, ensure that the `API_KEY` variable is set to `os.getenv("API_KEY")`.

## Usage

### Run_it_up.py GUI

- Run `python run_it_up.py`.
- Enter your first name when prompted.
- The GUI will display various buttons and options for managing satellite observations.

### API Interaction Script (api_interaction.py)

This script interacts with the N2YO API to fetch TLE data and visual pass information based on user inputs in the `run_it_up.py` GUI. It uses the API key from the `.env` file. The script can be run in non-interactive mode using command-line arguments:
- `--days`: Number of days ahead for observation (max 10)
- `--observation-window`: Observation window in minutes (default: 2)
- `--non-interactive`: Run the script without user interaction

### Other Scripts

- `pwi4_tle_observer.py`: Contains the core logic for satellite observation.
- `automated2.py`: A script that manages the overall observation process, including starting and stopping the observer script and handling dome operations.

## Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository.
2. Create a branch for your changes.
3. Commit your changes with meaningful commit messages.
4. Submit a pull request.


