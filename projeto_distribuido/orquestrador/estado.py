import os
import json

class GlobalState:
    def __init__(self):
        self.workers = ['localhost:50061', 'localhost:50062', 'localhost:50063']
        self.running_tasks = {}
        self.worker_heartbeats = {}

    def save_checkpoint(self):
        """Salva o estado atual em um arquivo JSON."""
        with open('checkpoint.json', 'w') as f:
            json.dump({
                "running_tasks": self.running_tasks,
                "workers": self.workers,
                "worker_heartbeats": self.worker_heartbeats
            }, f, indent=4)

    def load_from_checkpoint(self):
        """Carrega o estado a partir de um arquivo JSON, se existir."""
        if os.path.exists('checkpoint.json'):
            with open('checkpoint.json', 'r') as f:
                data = json.load(f)
                self.running_tasks = data.get("running_tasks", {})
                self.workers = data.get("workers", self.workers)
                self.worker_heartbeats = data.get("worker_heartbeats", {})