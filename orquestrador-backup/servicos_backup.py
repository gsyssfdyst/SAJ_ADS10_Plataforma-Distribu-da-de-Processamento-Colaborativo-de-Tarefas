import uuid
import grpc
import time
import json
from concurrent import futures

from projeto_distribuido.protos import tarefas_pb2, tarefas_pb2_grpc
from .estado_backup import BackupState

last_primary_heartbeat_time = {'time': None}

class SynchronizationServiceImpl(tarefas_pb2_grpc.SynchronizationServiceServicer):
    def __init__(self, backup_state):
        self.backup_state = backup_state

    def UpdateState(self, request, context):
        try:
            state_data = json.loads(request.state_json)
            self.backup_state.running_tasks = state_data.get("running_tasks", {})
            self.backup_state.workers = state_data.get("workers", [])
            self.backup_state.worker_heartbeats = state_data.get("worker_heartbeats", {})
            self.backup_state.save_checkpoint()
            return tarefas_pb2.StateUpdateResponse(success=True, message="Estado sincronizado com sucesso.")
        except Exception as e:
            return tarefas_pb2.StateUpdateResponse(success=False, message=f"Erro ao sincronizar estado: {str(e)}")

    def PrimaryHeartbeat(self, request, context):
        from google.protobuf import empty_pb2
        last_primary_heartbeat_time['time'] = time.time()
        return empty_pb2.Empty()
