import os
import json
import grpc
from protos import tarefas_pb2, tarefas_pb2_grpc

class GlobalState:
    def __init__(self):
        # Lista de endereços dos workers ativos
        self.workers = [
            'localhost:50061',
            'localhost:50062',
            'localhost:50063'
        ]
        # Dicionário para rastrear tarefas em execução
        self.running_tasks = {}
        self.worker_heartbeats = {}  # worker_id -> timestamp

    def save_checkpoint(self):
        with open('checkpoint.json', 'w') as f:
            json.dump({
                "running_tasks": self.running_tasks,
                "workers": self.workers,
                "worker_heartbeats": self.worker_heartbeats
            }, f)
        # Sincroniza com o backup após salvar localmente
        state_json = json.dumps({
            "running_tasks": self.running_tasks,
            "workers": self.workers,
            "worker_heartbeats": self.worker_heartbeats
        })
        self.sync_state_with_backup(state_json)

    def sync_state_with_backup(self, state_json):
        try:
            with grpc.insecure_channel('localhost:50052') as channel:
                stub = tarefas_pb2_grpc.SynchronizationServiceStub(channel)
                request = tarefas_pb2.StateUpdateRequest(state_json=state_json)
                response = stub.UpdateState(request)
                if response.success:
                    print("[SYNC] Estado sincronizado com backup.")
                else:
                    print(f"[SYNC] Falha ao sincronizar com backup: {response.message}")
        except Exception as e:
            print(f"[SYNC] Erro ao conectar/sincronizar com backup: {e}")

    def load_from_checkpoint(self):
        if os.path.exists('checkpoint.json'):
            with open('checkpoint.json', 'r') as f:
                data = json.load(f)
                self.running_tasks = data.get("running_tasks", {})
                self.workers = data.get("workers", [
                    'localhost:50061',
                    'localhost:50062',
                    'localhost:50063'
                ])
                self.worker_heartbeats = data.get("worker_heartbeats", {})
