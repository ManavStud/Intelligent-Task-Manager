# Intelligent Task Manager

# Introduction

The Intelligent Task Manager is an advanced Python-based tool designed to provide a comprehensive suite of functionalities for monitoring, analyzing, and securing system processes and network activity. Aimed at enhancing system performance, security, and privacy, this project incorporates a range of powerful modules that allow users to track process hierarchies, monitor network traffic, scan files for potential threats, and manage audio-visual device access. Through its integration with tools like MetaDefender for file scanning and advanced threat detection methods for network security, it serves as a multifaceted solution for users, developers, and IT administrators who seek robust control and insight into their system's behavior. This project offers a detailed and efficient way to handle tasks ranging from basic process monitoring to sophisticated network threat analysis and device control

# 1)Process and Network Monitoring

This project provides a Python script to log detailed process and network connection information, including privileges, I/O details, and runtime. The collected data is saved as a CSV file on the desktop for further analysis.

## Features

*   Logs process details such as PID, name, CPU/memory usage, privileges, and parent process info.
*   Tracks network connections associated with each process, including IP addresses, ports, and status.
*   Monitors active processes and logs their start and end times.
*   Outputs data in a CSV file format for easy analysis.

## Requirements

1.  **Operating System**: Windows
2.  **Python**: Version 3.6 or later
3.  **Required Libraries**:
    *   psutil
    *   wmi

## Installation

1.  Install the required Python libraries:

pip install psutil wmi

## Running the Script

1.  Open the script file process\_network\_logger.py in your preferred text editor.
2.  Adjust the duration of monitoring (in minutes) if needed by modifying the argument in start\_background\_task().
3.  Run the script:

python 1process\_and\_network\_monitoring.py

1.  The collected data will be saved as a CSV file named full\_process\_network\_info.csv on your desktop.

## How It Works

1.  **Privilege Detection**:
    *   Uses Windows APIs to query process privileges.
    *   Requires administrative privileges to access all processes.
2.  **Network Connection Retrieval**:
    *   Uses psutil to fetch current network connections.
3.  **Data Collection**:
    *   Gathers process attributes like memory usage, CPU usage, I/O counters, and runtime.
    *   Links processes with their associated network connections.
4.  **Output**:
    *   Saves detailed logs in a CSV file for review.

## CSV File Structure

The output CSV file contains the following columns:

*   pid: Process ID
*   name: Process name
*   exe: Executable path
*   cpu\_percent: CPU usage percentage
*   memory\_percent: Memory usage percentage
*   io\_counters: I/O statistics
*   create\_time: Process creation timestamp
*   username: Username of the process owner
*   status: Process status
*   priority\_class: Process priority
*   runtime: Process runtime in seconds
*   parent\_pid: Parent process ID
*   parent\_name: Parent process name
*   privileges: List of privileges enabled for the process
*   end\_time: Timestamp when the process ended
*   source\_ip: Source IP address for network connections
*   destination\_ip: Destination IP address for network connections
*   bytes\_sent: Total bytes sent by the process
*   bytes\_received: Total bytes received by the process
*   source\_port: Source port for network connections
*   destination\_port\_number: Destination port for network connections

## Notes

1.  **Admin Privileges**:
    *   Running the script as an administrator is recommended for complete process access.
2.  **Compatibility**:
    *   This script is designed for Windows systems and may not function correctly on other operating systems.
3.  **Performance**:
    *   The script runs in the background and may cause slight performance overhead due to continuous monitoring.

# 2) Process Chain and Monitoring

This project provides a Python script to monitor and manage process chains, track process hierarchies, and take specific actions when certain processes are detected. It can also terminate child processes that exceed a specified threshold.

## Features

*   Monitors processes continuously and detects specific processes by name.
*   Tracks the entire process hierarchy (parent-child relationships).
*   Executes custom actions when specific processes are detected.
*   Automatically terminates child processes that exceed a specified threshold of subprocesses.
*   Displays the process tree structure for visualization.

## Requirements

1.  **Operating System**: Windows
2.  **Python**: Version 3.12.5
3.  **Required Libraries**:
    *   psutil

## Installation

1.Install the required Python library:

pip install psutil

## Running the Script

1.  Open the script file process\_chain\_tracker.py in your preferred text editor.
2.  Add the process names and associated actions in the script. For example:

process\_chain.add\_to\_chain("Code.exe", action\_for\_process)

Replace Code.exe with the name of the process you want to monitor.

1.  Run the script:

python process\_chain\_tracker.py

1.  The script will run in the background, monitoring processes and building a process tree.
2.  To stop the script, press Ctrl+C. The tracked process tree will be displayed upon termination.

## How It Works

1.  **Process Monitoring**:
    *   Continuously scans active processes for those matching names in the chain.
2.  **Process Tree Building**:
    *   Builds a hierarchical tree of processes starting from a detected root process.
3.  **Action Execution**:
    *   Executes custom actions (e.g., logging, notifications) when a specific process is detected.
4.  **Child Process Management**:
    *   Terminates child processes exceeding a specified threshold of their own subprocesses.
5.  **Tree Visualization**:
    *   Displays the tracked process tree with indentation for better visualization.

## Example Output

When a process is detected and its tree is tracked, the output might look like this:

Process 'Code.exe' (PID: 1234) detected. Tracking its chain.
Process Tree:
Process 'Code.exe' (PID: 1234)
   Process 'ChildProcess1.exe' (PID: 5678)
      Process 'GrandChildProcess.exe' (PID: 91011)

## Notes

1.  **Threshold Management**:
    *   Adjust the threshold parameter in terminate\_excessive\_children to set the maximum allowed number of child processes.
2.  **Compatibility**:
    *   This script works on all major operating systems where psutil is supported.
3.  **Performance**:
    *   Monitoring processes continuously may cause slight performance overhead.

## Customization

1.  **Adding New Actions**:
    *   Define a function to handle the detected process:
    *   def my\_custom\_action(proc):
    *   print(f"Custom action for {proc.info\['name'\]} (PID: {proc.pid})")
    *   Add the process and action to the chain:
    *   process\_chain.add\_to\_chain("MyProcess.exe", my\_custom\_action)
2.  **Tree Visualization**:
    *   Use process\_chain.display\_process\_tree() to view the tracked process hierarchy.

# 3)Microphone and Camera Control and Monitoring Tool

## Overview

The Microphone and Camera Control and Monitoring Tool is designed to provide users with robust system-level control over their microphone and camera functionalities while offering real-time monitoring capabilities. Aimed at privacy-conscious individuals, developers, and IT administrators, this tool addresses the need for easy management of audio and video devices to mitigate unauthorized access risks. With an intuitive GUI and efficient backend processing, the tool empowers users to seamlessly manage device access and monitor applications utilizing the microphone.

## Features

*   **Microphone Control**: This feature leverages PowerShell scripts to modify registry keys that determine system-level microphone access. By directly updating the registry values for CapabilityAccessManager and applying related policies, users can ensure that unauthorized access is blocked or allowed based on their preference. This is crucial for safeguarding sensitive conversations from potential eavesdropping.  
    
*   **Camera Control**: Similar to the microphone control, this feature uses PowerShell scripts to adjust the registry settings for camera access. By toggling the registry values under the ConsentStore key, users can effectively enable or disable their camera, preventing malicious software or unauthorized apps from activating the camera without consent.  
    
*   **Combined Control**: This option combines the microphone and camera control scripts to allow users to toggle access for both devices simultaneously. It provides a convenient one-click solution for locking down audio and video inputs during sensitive tasks or meetings.  
    
*   **Real-time Monitoring**: Utilizing the pycaw library, this feature scans the audio sessions managed by the Windows Audio Service to identify active microphone usage. The psutil library is used to fetch detailed process information for each detected session, allowing users to pinpoint which applications are currently accessing the microphone. This feature is critical for real-time privacy assurance and intrusion detection.  
    
*   **Reset to Defaults**: This functionality restores the microphone and camera settings to their original states by removing custom registry keys and policies applied by the tool. It ensures that users can revert changes effortlessly without requiring manual intervention in the system settings.  
    
*   **User-Friendly GUI**: Built with Tkinter, the GUI presents users with a visually clear and straightforward interface. Buttons are color-coded to indicate actions (e.g., red for disabling, green for enabling), and a status label provides real-time feedback on operations.  
    
*   **Dynamic Updates**: The monitoring feature dynamically updates every 5 seconds to ensure users have the latest information about microphone usage. This ensures that any unauthorized access is detected promptly, enhancing the overall reliability and effectiveness of the tool.  
    
*   **Microphone Control**: Enable or disable system-level access to the microphone.  
    
*   **Camera Control**: Enable or disable system-level access to the camera.  
    
*   **Combined Control**: Simultaneously enable or disable both microphone and camera.  
    
*   **Real-time Monitoring**: Detect and display applications currently accessing the microphone.  
    
*   **Reset to Defaults**: Restore microphone and camera settings to their default state.  
    
*   **User-Friendly GUI**: A simple graphical interface for ease of use.  
    
*   **Dynamic Updates**: Refresh microphone usage data every 5 seconds.  
    

## Requirements

1.  **Python Version**: Python 3.8 or later.
2.  **Libraries**:
    *   tkinter (for GUI development)
    *   ctypes (for requesting admin privileges)
    *   subprocess (for running PowerShell commands)
    *   psutil (for process monitoring)
    *   pycaw (for audio session management)
3.  **Operating System**: Windows 10 or later.
4.  **Privileges**: Admin privileges are required for modifying system settings.

## Installation

1.  Ensure Python 3.8+ is installed on your system. You can verify the installed version by running the following command in your terminal or command prompt:

python --version

Install the required libraries using pip:  
pip install psutil pycaw

1.  Save the script to a file, e.g., mic\_cam\_control.py.

## How It Works

This tool was developed to address the increasing concerns surrounding unauthorized access to audio and video devices in modern computing environments. By providing a comprehensive suite of features, the tool empowers users to regain control over their privacy and ensures transparency in device usage.

From a technical perspective, the tool leverages registry modifications through PowerShell to enforce system-level restrictions on microphone and camera access. This ensures that the changes are robust and not easily overridden by standard application-level permissions. Real-time monitoring further enhances the tool's utility by identifying and displaying active microphone usage, making it an essential solution for detecting potential intrusions.

The primary motivation behind this development is to create a proactive defense mechanism for individuals and organizations against malicious software or unauthorized applications that exploit microphone and camera capabilities. With increasing reliance on video conferencing and virtual communication, ensuring the security of audio and video input devices has become paramount. This tool not only simplifies managing these aspects but also fosters awareness about potential vulnerabilities in digital systems.

1.  The script starts by checking for admin privileges using the ctypes library.
2.  It uses PowerShell commands executed via the subprocess library to modify Windows registry settings for microphone and camera access.
3.  The real-time monitoring feature uses the pycaw library to detect active audio sessions and psutil to fetch process details.
4.  A Tkinter GUI provides buttons for interacting with these features, and a status label displays the results of user actions.

## Output

The Graphical User Interface (GUI) for the Microphone and Camera Control and Monitoring Tool is designed for maximum usability and clarity. Built using the Tkinter library, the GUI integrates intuitive design principles to ensure that users of all technical levels can easily interact with the tool. Below are detailed aspects of the GUI layout and functionality:

### GUI Layout

1.  **Main Window**:  
    *   The main window is cleanly divided into distinct sections for microphone controls, camera controls, combined actions, and monitoring. Each section is visually separated with labels to enhance user navigation.
    *   Buttons are color-coded (green for enabling actions, red for disabling actions) to provide visual cues.
2.  **Control Buttons**:  
    *   Each button corresponds to a specific action, such as enabling or disabling the microphone and camera, or resetting all settings to their default state.
    *   The button text is concise, clearly indicating its functionality (e.g., "Enable Microphone").
3.  **Status Label**:  
    *   Located at the bottom of the window, the status label dynamically updates with feedback messages based on user interactions. Messages include "Microphone Disabled Successfully" or "Monitoring Active," ensuring the user is always informed of the system’s state.
4.  **Real-time Monitoring Panel**:  
    *   A dedicated section of the GUI displays a scrolling list of applications currently using the microphone. This panel refreshes every 5 seconds, ensuring the user receives up-to-date information.
5.  **Reset Defaults Button**:  
    *   A prominently placed button allows users to quickly revert all settings to their original states, offering a safety net for users who might inadvertently modify settings.

### Usability Features

*   **Admin Privileges Check**: Before launching the main GUI, the script verifies admin rights. If not detected, a pop-up alerts the user, ensuring critical features requiring elevated permissions are accessible.
*   **Error Handling**: If an operation fails (e.g., due to a service issue), the GUI displays a clear error message in the status label.
*   **Responsive Design**: The Tkinter framework ensures the GUI adapts to different screen resolutions, maintaining usability across devices.

### User Interaction Workflow

1.  Upon launching the application, the GUI presents all control options in an organized format.
2.  Users can click the relevant button (e.g., "Disable Camera") to perform the desired action. A status message confirms the success or failure of the operation.
3.  The monitoring panel automatically updates every 5 seconds, showing any active microphone usage. Users can use this information to identify unauthorized access.
4.  If users wish to reset changes, the "Reset Defaults" button provides an instant revert option, ensuring easy recovery.

### Technical Benefits of the GUI

*   **Streamlined Accessibility**: The GUI removes the need for manual PowerShell commands, providing non-technical users access to advanced system controls.
*   **Dynamic Feedback Loop**: Real-time updates and status messages ensure that users are always aware of the system state, reducing confusion.
*   **Integrated Monitoring**: The combination of control buttons and monitoring data in a single interface offers comprehensive device management from one location.

This GUI has been thoughtfully designed to combine functionality, clarity, and ease of use, making it a robust tool for managing and monitoring microphone and camera access.

*   **Control Actions**: A status message indicating success or failure for each operation.
*   **Real-time Monitoring**: A list of applications actively using the microphone, refreshed every 5 seconds.

## Notes

*   Changes to microphone and camera access persist until manually reverted or reset using the tool.
*   Some operations may require restarting services like Audiosrv to apply changes.

## Setup

1.  Open a terminal or command prompt with admin privileges.
2.  Navigate to the directory containing the script.
3.  Ensure all dependencies are installed as per the **Requirements** section.

## How to Run

Launch the script with admin privileges:  
python mic\_cam\_control.py

1.  Interact with the GUI to control microphone and camera settings or monitor usage.

## Implementation Details

The application combines Python libraries and PowerShell commands for effective system control:

*   **PowerShell Integration**: Used for registry modifications to enable or disable microphone and camera.
*   **Pycaw Integration**: Fetches active audio sessions to identify applications accessing the microphone.
*   **Tkinter GUI**: Provides an intuitive interface for users to interact with the tool.

## Functions

1.  **is\_admin()**: Checks if the script is running with admin privileges.
2.  **run\_powershell\_script(script)**: Executes a PowerShell script and captures the output.
3.  **disable\_microphone\_access()**: Disables microphone access via registry changes.
4.  **enable\_microphone\_access()**: Enables microphone access via registry changes.
5.  **disable\_camera\_access()**: Disables camera access via registry changes.
6.  **enable\_camera\_access()**: Enables camera access via registry changes.
7.  **disable\_both()**: Disables both microphone and camera access.
8.  **enable\_both()**: Enables both microphone and camera access.
9.  **reset\_defaults()**: Restores microphone and camera settings to their defaults.
10.  **get\_mic\_usage()**: Detects applications currently using the microphone.
11.  **update\_status(action, result)**: Updates the status label in the GUI.

## Troubleshooting

1.  **Admin Privileges Required**: Ensure the script is run with admin rights.
2.  **Missing Dependencies**: Install required libraries using pip.
3.  **Registry Access Denied**: Verify that the current user account has sufficient permissions.
4.  **Monitoring Issues**: Ensure pycaw and psutil are correctly installed.
5.  **Service Restart Issues**: Restart the Windows Audio service manually if necessary.

## Acknowledgments

*   **Pycaw Library**: For audio session management.
*   **Psutil Library**: For process monitoring.
*   **Tkinter**: For GUI development.
*   **Microsoft PowerShell**: For enabling registry-based system control.

## Execution Time

*   **Control Actions**: Instantaneous (less than 1 second per operation).
*   **Monitoring Refresh Interval**: 5 seconds.

# 4)MetaDefender File Scanner

This project scans running executable files on your system using the MetaDefender Cloud API and retrieves their scan reports. It ensures that files are only scanned once by maintaining a history of previously scanned files.

## Features

*   **Integration with MetaDefender Cloud API**: Upload files and retrieve scan reports.
*   **Round-robin API key usage**: Cycles through multiple API keys to avoid rate-limiting.
*   **Scan history**: Maintains a record of scanned files to prevent redundant scans.
*   **Automatic file detection**: Identifies all currently running executables on the system.

## Requirements

### Python Modules

*   psutil
*   requests
*   os
*   time
*   json

### Setup

1.  Install the required Python modules:
2.  pip install psutil requests
3.  Obtain API keys from MetaDefender Cloud.
    *   Sign up for an account [here](https://metadefender.opswat.com/).
    *   Generate API keys and add them to the API\_KEYS list in the script.
4.  Save the script in a file named meta\_defender\_scan.py or similar.

## How to Run

1.  Open a terminal or command prompt.
2.  Run the script using Python:
3.  python meta\_defender\_scan.py
4.  The script will:
    *   Identify all running executables.
    *   Upload files to the MetaDefender API for scanning.
    *   Retrieve scan reports and save them.
    *   Maintain a history of scanned files in scan\_history.json.

## Files

*   **meta\_defender\_scan.py**: Main script.
*   **scan\_history.json**: File storing scan history. Automatically created during runtime.

## Configuration

### API Keys

Add your API keys to the API\_KEYS list in the script. Example:

API\_KEYS = \[

'key1',

'key2',

'key3'

\]

### Scan History

The scan\_history.json file will store a dictionary with the format:

{

"file\_path": "data\_id"

}

## Implementation Details

### Functions

#### load\_scan\_history()

*   Loads the scan history from scan\_history.json.

#### save\_scan\_history(scan\_history)

*   Saves updated scan history to scan\_history.json.

#### get\_next\_api\_key(index)

*   Cycles through API keys in a round-robin manner.

#### scan\_file(file\_path, api\_key)

*   Uploads a file to MetaDefender Cloud for scanning.

#### get\_scan\_report(data\_id, api\_key)

*   Polls MetaDefender Cloud for the scan report of a given data\_id.

#### get\_all\_running\_files()

*   Identifies all currently running executable files.

#### main()

*   Orchestrates the scanning process.

## Notes

*   Ensure you have permission to scan the files running on your system.
*   API keys may have limitations based on your MetaDefender Cloud subscription.
*   The script skips files that have already been scanned.
*   Scans may take some time depending on file size and server load.

## Example Output

1.  Detects 10 running files.
2.  Uploads each file to MetaDefender.
3.  Displays progress updates and final reports.

## Troubleshooting

*   **Issue**: Missing dependencies.
    *   **Solution**: Ensure psutil and requests modules are installed.
*   **Issue**: API key errors.
    *   **Solution**: Verify your API keys are valid and have not exceeded rate limits.
*   **Issue**: Scan report retrieval timeout.
    *   **Solution**: Increase the wait time between polling attempts in get\_scan\_report().

## Acknowledgments

*   **MetaDefender Cloud API**: For providing the scanning service.
*   **Python Community**: For helpful libraries like psutil and requests.

# 5)IP Threat Analysis

This Python-based system captures network packets in real-time, extracts source and destination IPs, and analyzes them using multiple threat detection methods, including:

1.  **Bloom Filter Blocklist**: Checks against a locally maintained blocklist.
2.  **Google Safe Browsing API**: Queries Google’s threat intelligence for malicious activities.
3.  **Reputation Check**: Verifies the IP's reputation based on predefined criteria.

Results are logged into a CSV file for future reference, making this tool highly efficient for network monitoring and malicious IP detection.

## Features

*   **Real-Time Packet Capture**: Monitors live network traffic to extract IPs.
*   **Threat Analysis Methods**:
    *   Bloom Filter for fast malicious IP lookups.
    *   Google Safe Browsing API for comprehensive threat detection.
    *   Simple reputation-based checks.
*   **Live Logging**: Saves analyzed results in a user-defined CSV file on the desktop.
*   **Periodic Blocklist Updates**: Automatically downloads and processes the latest blocklists from trusted sources every 24 hours.
*   **User-Controlled Execution**: Allows the user to stop the program anytime by pressing the S key.
*   **Time-Bound Execution**: The system stops automatically after running for one minute unless the user stops it earlier.

## Prerequisites

*   Python 3.12.5
*   Required Python libraries:
    *   scapy for packet sniffing
    *   requests for API calls and downloading blocklists
    *   pybloom\_live for efficient Bloom Filter operations
    *   msvcrt (Windows-specific) for detecting key presses
*   Administrative privileges (to enable packet capture using Scapy)

## Setup

1.  Install required dependencies:

pip install scapy requests pybloom-live

1.  Replace the placeholder your\_google\_safe\_browsing\_api\_key in the script with your actual API key from Google Safe Browsing.
2.  Run the program:

ip\_threat\_analysis.ipynb

1.  Enter the desired name for the CSV output file when prompted.

## How It Works

1.  **Blocklist Initialization**:  
    Downloads blocklists from multiple sources and stores them in a Bloom Filter for efficient lookup.
2.  **Packet Capture**:  
    Captures live network packets and extracts the source and destination IP addresses.
3.  **Threat Analysis**:  
    Each IP is analyzed using:
    *   **Bloom Filter Check**: Compares against the local blocklist.
    *   **Google Safe Browsing API**: Checks for known threats via Google’s database.
    *   **Reputation Check**: Flags IPs based on a hardcoded list of malicious IPs.
4.  **Result Logging**:  
    Logs analyzed IPs, their reputation status, and method-specific flags into the specified CSV file.
5.  **Program Control**:
    *   Press S to stop the program manually.
    *   The program automatically halts after one minute of execution.

## CSV File Format

The results are logged into a CSV file with the following columns:

*   IP: The analyzed IP address.
*   Reputation: Final decision (Clean or Malicious).
*   Method Flags: Details of which methods flagged the IP as malicious.
*   Time: Timestamp of when the analysis was logged.

Example:

| IP | Reputation | Method Flags | Time |
| --- | --- | --- | --- |
| 8.8.8.8 | Malicious | {"Bloom Filter": "Clean", } | Sat Dec 24 2024 12:00:00 |

## Customizing the Script

*   **Blocklist Sources**: Add or remove blocklist URLs in the blocklist\_urls list.
*   **Execution Time**: Adjust the runtime by modifying the start\_time check in the main function.
*   **Reputation Check**: Update the malicious\_ips list in the check\_ip\_reputation function.

## Known Limitations

*   The program currently uses a hardcoded reputation list for some checks, which may not reflect all real-world scenarios.
*   Requires administrative privileges to capture packets using Scapy.
*   The Google Safe Browsing API integration requires a valid API key and may have rate limits.

## Future Improvements

*   Integrate additional APIs for IP reputation analysis.
*   Add cross-platform support for key-press detection.
*   Enhance the blocklist parsing for different formats.

# 6)USB and Audio Device Monitor

## Overview

The **USB and Audio Device Monitor** is a Python-based script that utilizes the WMI (Windows Management Instrumentation) library to track and display connected USB devices and audio devices. This program provides a simple and efficient way to monitor system peripherals.

## Features

*   Lists all connected USB devices.
*   Lists all audio devices available on the system.
*   Leverages the WMI library for system-level hardware monitoring.
*   Lightweight and easy to run on any Windows system.

## Prerequisites

*   **Operating System**: Windows (as WMI is Windows-specific).
*   **Python Version**: Python 3.12.5 or later.
*   **Required Python Library**:

*   wmi: For accessing and querying Windows Management Instrumentation.

To install the WMI library, use:

pip install wmi

## Setup

1.  **Install Python**: Ensure Python is installed and configured on your system.
2.  **Install Dependencies**: Run the following command to install the required library:
3.  pip install wmi
4.  **Run the Script**: Save the script as device\_monitor.py and execute it using:
5.  python device\_monitor.py

## How It Works

1.  **USB Device Monitoring**:

*   Queries the Win32\_USBControllerDevice class via WMI.
*   Iterates through all USB devices and prints their names.

3.  **Audio Device Monitoring**:

*   Queries the Win32\_SoundDevice class via WMI.
*   Fetches and prints the name of each detected audio device.

5.  **Execution**:

*   When run, the script displays a list of USB devices and audio devices directly in the console.

## Usage

1.  **Monitor USB Devices**: Run the script to list all USB devices connected to your system.
2.  **Monitor Audio Devices**: The script will also list all audio devices detected on your system.

## Sample Output

When executed, the script might output:

USB Devices:

USB Device: Generic USB Hub

USB Device: USB Composite Device

Audio Devices:

Audio Device: Realtek High Definition Audio

Audio Device: NVIDIA High Definition Audio

## Customizing the Code

*   **Device Filtering**: Modify the script to filter devices by specific properties (e.g., device type, manufacturer).
*   **Logging**: Extend the script to log the output to a file for later review.
*   **Device Status Monitoring**: Add functionality to detect when a device is connected or disconnected in real-time.

## Known Limitations

*   **OS Dependency**: This script only works on Windows systems due to its reliance on the WMI library.
*   **Output Details**: The script currently displays only the device names. Additional details (e.g., device status or manufacturer) can be extracted but are not included by default.

## Future Improvements

1.  **Real-Time Monitoring**: Implement a feature to detect and log device connection/disconnection events.
2.  **Enhanced Device Details**: Add functionality to display additional device information like manufacturer, status, and driver version.
3.  **Cross-Platform Support**: Explore libraries like pyudev for extending functionality to Linux.
4.  **GUI Integration**: Develop a user-friendly GUI for monitoring and managing connected devices.

# 7)Active Window Input Tracker

## Overview

The Active Window Input Tracker is a Python-based tool that tracks and stores user keyboard inputs for each active window separately. This program allows you to monitor typing activity on multiple windows simultaneously and organizes the inputs by the window titles.

## Features

*   Tracks keyboard inputs in real-time for all active windows.
*   Organizes and stores inputs based on the title of the active window.
*   Handles special keys such as Space and Backspace.
*   Provides a user-friendly way to monitor and update text for each window.
*   Allows the program to be terminated gracefully by pressing the F1 key.

## Prerequisites

*   Python 3.12.5
*   Required Python libraries:
    *   keyboard: For capturing global keyboard events.
    *   pygetwindow: For detecting the active window.

## Setup

1.  Install the required dependencies:

pip install keyboard pygetwindow

1.  Run the program:

keylogger.ipynb

## How It Works

1.  **Key Event Listener**:
    *   The script listens to global key presses using the keyboard library.
    *   Captures characters, spaces, and backspaces.
2.  **Window Tracking**:
    *   The program uses pygetwindow to detect the currently active window.
    *   Input is stored separately for each window, identified by its title.
3.  **Real-Time Input Display**:
    *   As you type, the program displays the current input for the active window in the console.
4.  **Program Termination**:
    *   Press F1 to gracefully stop the program.

## Usage

1.  Start the program, and type in different windows (e.g., browsers, text editors, terminal).
2.  The script will track and print inputs for each active window separately in the console.
3.  To stop the program, press the F1 key.

## Sample Output

While running, the console might display:

Press 'F1' to stop the program...

Current Input in 'Untitled - Notepad': Hello

Current Input in 'Google Chrome': Searching for Active Window Tracker

Current Input in 'Terminal': python example.py

## Customizing the Code

*   **Special Key Handling**:
    *   Modify how specific keys (e.g., Enter, Tab) are handled in the on\_key\_event function.
*   **Window Title Management**:
    *   Update or format the active window titles as needed (e.g., truncate long titles).
*   **Input Processing**:
    *   Extend the code to save inputs to a file or database for further analysis.

## Known Limitations

*   The pygetwindow library might not detect active windows correctly on certain operating systems or configurations.
*   The program currently does not support non-character keys like Shift, Ctrl, or Alt.

## Future Improvements

*   Add support for non-character keys.
*   Implement cross-platform compatibility for window detection.
*   Save input logs to a file for later review.
*   Create a GUI to display inputs for each window dynamically.

# Conclusion

The **Intelligent Task Manager** proves to be a versatile and essential tool for improving system security, monitoring, and privacy. By providing an all-in-one platform for process and network monitoring, file scanning, and device access control, it equips users with the tools necessary to effectively manage system operations and mitigate security risks. Whether it's tracking process chains, detecting malicious IPs, or ensuring privacy with microphone and camera controls, the project empowers users to maintain a secure and efficient digital environment. With its comprehensive capabilities, the Intelligent Task Manager offers not only real-time protection but also a proactive approach to system management, making it an invaluable asset for both personal and professional use.
