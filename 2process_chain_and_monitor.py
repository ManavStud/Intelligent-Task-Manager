import psutil
import time
from threading import Thread

class ProcessChain:
    def __init__(self):
        self.chain = {}  # Mapping process names to actions
        self.running = True
        self.process_tree = {}  # Store the process hierarchy

    def add_to_chain(self, process_name, action):
        """
        Add a process to the chain and associate it with an action.

        :param process_name: Name of the process to monitor.
        :param action: A callable action to execute when the process is detected.
        """
        self.chain[process_name] = action

    def monitor_processes(self):
        """Continuously monitors processes to track and log their chain."""
        tracked_pids = set()
        while self.running:
            current_processes = {proc.pid: proc for proc in psutil.process_iter(attrs=['pid', 'ppid', 'name'])}

            # Check for processes in the chain
            for process_name, action in list(self.chain.items()):
                for proc in current_processes.values():
                    if proc.info['name'] == process_name and proc.pid not in tracked_pids:
                        tracked_pids.add(proc.pid)
                        print(f"Process '{process_name}' detected (PID: {proc.pid}). Tracking its chain.")
                        action(proc)
                        self.build_process_tree(proc, current_processes)

                        # Check and terminate if subprocess count exceeds threshold
                        self.terminate_excessive_children(proc.pid, current_processes, threshold=20)

            time.sleep(2)  # Check every 2 seconds

    def build_process_tree(self, root_process, current_processes):
        """
        Build a tree of processes starting from the root_process.

        :param root_process: The root process to track.
        :param current_processes: A dictionary of all current processes.
        """
        root_pid = root_process.pid
        self.process_tree[root_pid] = {'name': root_process.info['name'], 'children': []}

        queue = [root_pid]
        while queue:
            parent_pid = queue.pop(0)
            for proc in current_processes.values():
                if proc.info['ppid'] == parent_pid:
                    self.process_tree[parent_pid]['children'].append(proc.pid)
                    self.process_tree[proc.pid] = {'name': proc.info['name'], 'children': []}
                    queue.append(proc.pid)

    def terminate_excessive_children(self, pid, current_processes, threshold):
        """
        Terminate child processes that have more than the allowed number of their own child processes.

        :param pid: PID of the root process.
        :param current_processes: A dictionary of all current processes.
        :param threshold: Maximum allowed number of child processes.
        """
        queue = [pid]
        while queue:
            parent_pid = queue.pop(0)
            child_processes = [proc for proc in current_processes.values() if proc.info['ppid'] == parent_pid]

            for child_proc in child_processes:
                grandchild_count = sum(1 for proc in current_processes.values() if proc.info['ppid'] == child_proc.pid)

                if grandchild_count > threshold:
                    print(f"Child process (PID: {child_proc.pid}) has too many subprocesses ({grandchild_count} > {threshold}). Terminating...")
                    self.terminate_process(child_proc.pid, current_processes)

                queue.append(child_proc.pid)

    def terminate_process(self, pid, current_processes):
        """
        Terminate a single process.

        :param pid: PID of the process to terminate.
        :param current_processes: A dictionary of all current processes.
        """
        try:
            psutil.Process(pid).terminate()
            print(f"Terminated process (PID: {pid}).")
        except psutil.NoSuchProcess:
            print(f"Process (PID: {pid}) already terminated.")

    def display_process_tree(self):
        """
        Display the tracked process tree with indentation for clarity.
        """
        def recursive_display(pid, level=0):
            process_info = self.process_tree.get(pid)
            if process_info:
                print("    " * level + f"Process '{process_info['name']}' (PID: {pid})")
                for child_pid in process_info['children']:
                    recursive_display(child_pid, level + 1)

        if not self.process_tree:
            print("No processes were tracked.")
            return

        print("\nProcess Tree:")
        root_processes = [
            pid for pid in self.process_tree
            if not any(pid in info['children'] for info in self.process_tree.values())
        ]

        if not root_processes:
            print("No root processes found in the tracked tree.")
            return

        for root_pid in root_processes:
            recursive_display(root_pid)

    def stop(self):
        """Stops the monitoring."""
        self.running = False

# Example Actions
def action_for_process(proc):
    print(f"Action: Tracking chain for process '{proc.info['name']}' (PID: {proc.pid})")
    # Placeholder for additional actions (e.g., logging, notifications)

# Setup and Execution
if __name__ == "__main__":
    process_chain = ProcessChain()

    # Add processes and their associated actions to the chain
    process_chain.add_to_chain("Code.exe", action_for_process)  # Replace "chrome.exe" with "Code.exe" for VSCode

    # Start monitoring in a separate thread
    monitor_thread = Thread(target=process_chain.monitor_processes)
    monitor_thread.start()

    try:
        while True:
            time.sleep(1)  # Keep the main thread alive
    except KeyboardInterrupt:
        print("\nStopping the process chain.")
        process_chain.stop()
        monitor_thread.join()

        # Display the ordered process tree
        process_chain.display_process_tree()
