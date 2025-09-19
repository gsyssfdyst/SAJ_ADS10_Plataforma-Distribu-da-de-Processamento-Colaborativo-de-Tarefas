import uuid
import grpc
import time
import json
from concurrent import futures

from projeto_distribuido.protos import tarefas_pb2, tarefas_pb2_grpc
from projeto_distribuido.orquestrador.estado import GlobalState

class TaskOrchestratorService(tarefas_pb2_grpc.TaskOrchestratorServicer):
    def __init__(self, global_state):
        self.state = global_state
        self._worker_index = 0

    def _sync_state_with_backup(self):
        state_json = json.dumps({
            "running_tasks": self.state.running_tasks,
            "workers": self.state.workers,
            "worker_heartbeats": self.state.worker_heartbeats
        })
        try:
            with grpc.insecure_channel('localhost:50052') as channel:
                stub = tarefas_pb2_grpc.SynchronizationServiceStub(channel)
                request = tarefas_pb2.StateUpdateRequest(state_json=state_json)
                stub.UpdateState(request)
        except Exception:
            pass # Silencia o erro se o backup não estiver no ar

    def get_next_worker(self):
        if not self.state.workers:
            return None
        worker = self.state.workers[self._worker_index]
        self._worker_index = (self._worker_index + 1) % len(self.state.workers)
        return worker

    def SubmitTask(self, request, context):
        valid_tokens = {'user1': 'token_valido_123'}
        if not request.user_id or valid_tokens.get(request.user_id) != request.user_token:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token inválido.")

        task_id = str(uuid.uuid4())
        worker_addr = self.get_next_worker()
        if not worker_addr:
            context.abort(grpc.StatusCode.UNAVAILABLE, "Nenhum worker disponível.")
        
        print(f"Tarefa [{task_id}] atribuída ao worker [{worker_addr}]")
        self.state.running_tasks[task_id] = {"worker_id": worker_addr, "status": "EM_EXECUCAO"}
        self.state.save_checkpoint()
        self._sync_state_with_backup()

        return tarefas_pb2.TaskResponse(task_id=task_id, status="RECEBIDA")

    def CheckTaskStatus(self, request, context):
        task_info = self.state.running_tasks.get(request.task_id)
        if task_info:
            return tarefas_pb2.StatusResponse(task_id=request.task_id, status=task_info.get("status"))
        else:
            context.abort(grpc.StatusCode.NOT_FOUND, "Tarefa não encontrada.")

class WorkerService(tarefas_pb2_grpc.WorkerServiceServicer):
    def __init__(self, state):
        self.state = state

    def SendHeartbeat(self, request, context):
        worker_id = request.worker_id
        self.state.worker_heartbeats[worker_id] = time.time()
        if worker_id not in self.state.workers:
            self.state.workers.append(worker_id)
            print(f"Novo worker registrado: {worker_id}")
        return tarefas_pb2.HeartbeatResponse()