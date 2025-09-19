import os
import json

class BackupState:
    def __init__(self):
        self.workers = [
            'localhost:50061',
            'localhost:50062',
            'localhost:50063'
        ]
        self.running_tasks = {}
        self.worker_heartbeats = {}

    def save_checkpoint(self):
        with open('backup_checkpoint.json', 'w') as f:
            json.dump(self.running_tasks, f)

    def load_from_checkpoint(self):
        if os.path.exists('backup_checkpoint.json'):
            with open('backup_checkpoint.json', 'r') as f:
                self.running_tasks = json.load(f)
