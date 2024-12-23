import os
import psutil
import requests
import time
import json

# List of MetaDefender Cloud API keys
API_KEYS = [
    '37f3f4fec8df08e601bffae2c7c4de0f',
    '7ee27d5a5a4c23317f24aa2888a07eb7',
    'e095257a77ba082d0ecf7f2c16b83755',
    '7907bca8f96cc3bc9ed89251929db9c1',
    '19cc0624b148ca10e60cf738083326a1',
    '6c15866734c946c090b20e593660904e',
    'a38344e414864aadbaaf486c89a61bcb'
    # Add more API keys here
]
BASE_URL = 'https://api.metadefender.com/v4/file'

# File path to store scan history
SCAN_HISTORY_FILE = 'scan_history.json'

# Load scan history from a file if it exists
def load_scan_history():
    if os.path.exists(SCAN_HISTORY_FILE):
        with open(SCAN_HISTORY_FILE, 'r') as file:
            return json.load(file)
    return {}

# Save scan history to a file
def save_scan_history(scan_history):
    with open(SCAN_HISTORY_FILE, 'w') as file:
        json.dump(scan_history, file)

# Function to get the next API key in a round-robin fashion
def get_next_api_key(index):
    return API_KEYS[index % len(API_KEYS)], index + 1

# Function to scan a file with MetaDefender
def scan_file(file_path, api_key):
    headers = {
        'apikey': api_key,
    }
    with open(file_path, 'rb') as file_data:
        response = requests.post(BASE_URL, headers=headers, files={'file': file_data})
        if response.status_code == 200:
            return response.json().get('data_id')
        else:
            print(f"Failed to upload {file_path}. Status code: {response.status_code}")
            return None

# Function to get the scan report for a file
def get_scan_report(data_id, api_key):
    headers = {
        'apikey': api_key,
    }
    report_url = f"{BASE_URL}/{data_id}"
    while True:
        response = requests.get(report_url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get('scan_results', {}).get('progress_percentage', 0) == 100:
                return result
            else:
                print(f"Scanning in progress for data_id: {data_id}. Waiting for 5 seconds.")
                time.sleep(5)
        else:
            print(f"Failed to retrieve report for data_id: {data_id}. Status code: {response.status_code}")
            return None

# Function to get all currently running files
def get_all_running_files():
    files = []
    for process in psutil.process_iter(['exe']):
        try:
            exe_path = process.info['exe']
            if exe_path and os.path.isfile(exe_path):
                files.append(exe_path)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            # Skip processes we can't access
            continue
    return files

# Main function
def main():
    # Load scan history
    scan_history = load_scan_history()
    api_key_index = 0  # To cycle through API keys

    running_files = get_all_running_files()
    print(f"Found {len(running_files)} running files.")

    for file_path in running_files:
        # Check if file has already been scanned
        if file_path in scan_history:
            print(f"\nFile '{file_path}' has already been scanned. Skipping.")
            continue

        api_key, api_key_index = get_next_api_key(api_key_index)
        print(f"\nScanning file: {file_path} using API key index {api_key_index - 1}")
        data_id = scan_file(file_path, api_key)
        if data_id:
            report = get_scan_report(data_id, api_key)
            if report:
                print(f"Scan report for {file_path}:")
                print(report)
                # Add file path and data_id to scan history
                scan_history[file_path] = data_id
                save_scan_history(scan_history)
            else:
                print(f"Failed to get report for {file_path}")
        else:
            print(f"Failed to scan file: {file_path}")

if __name__ == "__main__":
    main()
