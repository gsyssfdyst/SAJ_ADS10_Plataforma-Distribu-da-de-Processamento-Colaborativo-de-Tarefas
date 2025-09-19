import uuid
import grpc
import time
import json
from concurrent import futures

from protos import tarefas_pb2, tarefas_pb2_grpc
from orquestrador_backup.estado_backup import BackupState

last_primary_heartbeat = None  # variável global para armazenar o último heartbeat do primário

class BackupTaskOrchestratorService(tarefas_pb2_grpc.TaskOrchestratorServicer):
    def __init__(self):
        self.state = BackupState()
        self._worker_index = 0

    def get_next_worker(self):
        if not self.state.workers:
            return None
        worker = self.state.workers[self._worker_index]
        self._worker_index = (self._worker_index + 1) % len(self.state.workers)
        return worker

    def SubmitTask(self, request, context):
        if not request.user_id or not request.user_token:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "user_id e user_token são obrigatórios.")

        valid_tokens = {'user1': 'token_valido_123'}
        if valid_tokens.get(request.user_id) != request.user_token:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token inválido para o usuário.")

        task_id = str(uuid.uuid4())
        print(f"[BACKUP] Tarefa recebida e autenticada: user_id={request.user_id}, task_id={task_id}")

        worker_addr = self.get_next_worker()
        print(f"[BACKUP] Tarefa [{task_id}] atribuída ao worker [{worker_addr}] via Round Robin.")

        self.state.running_tasks[task_id] = {
            "worker_id": worker_addr,
            "status": "EM_EXECUCAO"
        }
        self.state.save_checkpoint()

        return tarefas_pb2.TaskResponse(
            task_id=task_id,
            status="RECEBIDA",
            message="Tarefa recebida com sucesso (backup)."
        )

class BackupWorkerService(tarefas_pb2_grpc.WorkerServiceServicer):
    def __init__(self, state):
        self.state = state

    def SendHeartbeat(self, request, context):
        worker_id = request.worker_id
        self.state.worker_heartbeats[worker_id] = time.time()
        print(f"[BACKUP] Heartbeat recebido de {worker_id} em {self.state.worker_heartbeats[worker_id]}")
        return tarefas_pb2.HeartbeatResponse()

class SynchronizationServiceImpl(tarefas_pb2_grpc.SynchronizationServiceServicer):
    def __init__(self, backup_state):
        self.backup_state = backup_state

    def UpdateState(self, request, context):
        try:
            state_data = json.loads(request.state_json)
            self.backup_state.running_tasks = state_data.get("running_tasks", {})
            self.backup_state.workers = state_data.get("workers", [])
            self.backup_state.worker_heartbeats = state_data.get("worker_heartbeats", {})
            with open('checkpoint_backup.json', 'w') as f:
                json.dump({
                    "running_tasks": self.backup_state.running_tasks,
                    "workers": self.backup_state.workers,
                    "worker_heartbeats": self.backup_state.worker_heartbeats
                }, f)
            return tarefas_pb2.StateUpdateResponse(success=True, message="Estado sincronizado com sucesso.")
        except Exception as e:
            return tarefas_pb2.StateUpdateResponse(success=False, message=f"Erro ao sincronizar estado: {str(e)}")

    def PrimaryHeartbeat(self, request, context):
        global last_primary_heartbeat
        last_primary_heartbeat = time.time()
        print(f"[BACKUP] Heartbeat do primário recebido em {last_primary_heartbeat}")
        return tarefas_pb2.google_dot_protobuf_dot_empty__pb2.Empty()
