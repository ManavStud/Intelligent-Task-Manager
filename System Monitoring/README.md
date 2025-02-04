# System Monitoring

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![License](https://img.shields.io/badge/License-MIT-green)

The **System Monitoring module** is a modern, feature-rich desktop application built using Python's `tkinter` library. It provides real-time monitoring and management of system processes, resource usage, security commands, backend processes, and IP connections. The application is designed to be user-friendly, visually appealing, and highly functional.

## Table of Contents
1. [Features](#features)
2. [Installation](#installation)
3. [Dependencies](#dependencies)
4. [Usage](#usage)
5. [Screenshots](#screenshots)
6. [Contributing](#contributing)
7. [License](#license)

---

## Features

### 1. Task Manager
- Displays all running processes with detailed information:
  - Process Name, PID, Executable Path, User, Current Working Directory (CWD), Command-Line Arguments, Open Files, CPU Usage, Memory Usage, and Network Connections.
- Search functionality to filter processes by name or other attributes.
- Ability to terminate processes by specifying their PID.

### 2. Resource Monitor
- Real-time monitoring of system resources:
  - CPU Usage
  - Memory Usage
  - Disk Usage
- Visual progress bars for easy interpretation of resource consumption.

### 3. Security Commands
- Execute system-level commands such as listing scheduled tasks.
- Displays detailed information about scheduled tasks, including task name, next run time, status, start time, duration, and timestamp.

### 4. Backend Commands
- Monitors all active processes and categorizes them into:
  - All Processes
  - System32 Processes
- Provides details such as PID, Name, Command, Start Time, Duration, Status, and Source File.

### 5. IP Monitor
- Tracks active IPv4 and IPv6 connections in real-time.
- Displays connection details such as IP Address, Status (Connected/Disconnected), Connected At, Disconnected At, Session Duration, and Session Data (Bytes Sent/Received).

---

## Installation

### Prerequisites
- Python 3.8 or higher installed on your system.
- Pip (Python package manager) should be available.

### Steps to Install
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/intelligent-task-manager.git
   cd intelligent-task-manager
