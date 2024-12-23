import subprocess

def spawn_processes(n):
    """Spawns `n` subprocesses."""
    processes = []
    try:
        for i in range(n):
            # Spawn a subprocess that runs the child script
            process = subprocess.Popen(
                ["python", "child_process.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            processes.append(process)
            print(f"Spawned process PID: {process.pid}")

        print("\nSubprocesses are running. Check your Task Manager.")
        print("Press Ctrl+C to terminate the main program.")

        # Keep the main program running
        while True:
            pass
    except KeyboardInterrupt:
        print("\nTerminating subprocesses...")
        for process in processes:
            process.terminate()
            process.wait()
        print("All subprocesses terminated.")

if __name__ == "__main__":
    n = int(input("Enter the number of subprocesses to spawn: "))
    spawn_processes(n)
