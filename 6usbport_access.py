import wmi

def monitor_usb_devices():
    c = wmi.WMI()
    
    print("USB Devices:")
    for usb_device in c.Win32_USBControllerDevice():
        print(f"USB Device: {usb_device.Dependent.Name}")

def monitor_audio_devices():
    c = wmi.WMI()
    
    print("\nAudio Devices:")
    for audio_device in c.Win32_SoundDevice():
        print(f"Audio Device: {audio_device.Name}")

if __name__ == "__main__":
    monitor_usb_devices()
    monitor_audio_devices()
