import time
import os

if __name__ == "__main__":
    print("Child process started. PID:", os.getpid())
    while True:
        time.sleep(1)  # Infinite loop to keep the subprocess alive
