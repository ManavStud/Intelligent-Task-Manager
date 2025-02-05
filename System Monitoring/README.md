# System Monitoring

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![License](https://img.shields.io/badge/License-MIT-green)

The **System Monitoring module** is a modern, feature-rich desktop application built using Python's `tkinter` library. It provides real-time monitoring and management of system processes, resource usage, security commands, backend processes, and IP connections. The application is designed to be user-friendly, visually appealing, and highly functional.

## Table of Contents
1. Features
2. Installation
3. Dependencies
4. Usage
5. Screenshots
6. Contributing
7. License

---

### Features

#### 1. Task Manager
- Displays all running processes with detailed information:
  - Process Name, PID, Executable Path, User, Current Working Directory (CWD), Command-Line Arguments, Open Files, CPU Usage, Memory Usage, and Network Connections.
- Search functionality to filter processes by name or other attributes.
- Ability to terminate processes by specifying their PID.

#### 2. Resource Monitor
- Real-time monitoring of system resources:
  - CPU Usage
  - Memory Usage
  - Disk Usage
- Visual progress bars for easy interpretation of resource consumption.

#### 3. Security Commands
- Execute system-level commands such as listing scheduled tasks.
- Displays detailed information about scheduled tasks, including task name, next run time, status, start time, duration, and timestamp.

#### 4. Backend Commands
- Monitors all active processes and categorizes them into:
  - All Processes
  - System32 Processes
- Provides details such as PID, Name, Command, Start Time, Duration, Status, and Source File.

#### 5. IP Monitor
- Tracks active IPv4 and IPv6 connections in real-time.
- Displays connection details such as IP Address, Status (Connected/Disconnected), Connected At, Disconnected At, Session Duration, and Session Data (Bytes Sent/Received).

---

### Installation

### Prerequisites
- Python 3.8 or higher installed on your system.
- Pip (Python package manager) should be available.

### Steps to Install
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/intelligent-task-manager.git
   cd intelligent-task-manager

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt

3.Once the dependencies are installed, you're ready to run the application.

### Steps to Install

The following dependencies are required to run the System Monitoring module:

tkinter: The core library for building the GUI.
psutil: A library used for retrieving information on system utilization (CPU, memory, disk, network).
psutil: Required for accessing process-related information such as CPU usage, memory, and more.

You can install all the dependencies by running:

### Usage

To start using the application, run the main Python script:

### Dependencies

This project requires the following dependencies to run:

1. **tkinter**:  
   - Tkinter is the standard Python interface to the Tk GUI toolkit. It is used to create graphical user interfaces (GUIs) in Python applications.
   - Tkinter is included with most Python distributions, so it is often already installed.

   Installation (if not installed):
   ```bash
   pip install tk

### Contributing

We welcome contributions to the System Monitoring module. If you have ideas for features or fixes, feel free to open an issue or submit a pull request.

### How to Contribute

Fork the repository.
Create a new branch (git checkout -b feature/your-feature).
Make your changes and commit them (git commit -m 'Add new feature').
Push to your forked repository (git push origin feature/your-feature).
Open a pull request.

Please make sure to follow the coding style and conventions used in the project.

### License

This project is licensed under the MIT License - see the LICENSE file for details.

This version of the README includes sections for Features, Installation, Dependencies, Usage, Screenshots, Contributing, and License. You can add or modify any sections based on your needs.

