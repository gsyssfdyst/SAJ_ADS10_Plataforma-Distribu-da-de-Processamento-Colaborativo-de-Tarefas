import uuid
import grpc
import time
from concurrent import futures

from protos import tarefas_pb2, tarefas_pb2_grpc
from orquestrador.estado import GlobalState

class TaskOrchestratorService(tarefas_pb2_grpc.TaskOrchestratorServicer):
    def __init__(self):
        self.state = GlobalState()
        self._worker_index = 0

    def get_next_worker(self):
        if not self.state.workers:
            return None
        worker = self.state.workers[self._worker_index]
        self._worker_index = (self._worker_index + 1) % len(self.state.workers)
        return worker

    def SubmitTask(self, request, context):
        # Verifica se user_id e user_token não estão vazios
        if not request.user_id or not request.user_token:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "user_id e user_token são obrigatórios.")

        # Simula autenticação básica
        valid_tokens = {'user1': 'token_valido_123'}
        if valid_tokens.get(request.user_id) != request.user_token:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token inválido para o usuário.")

        # Gera um ID de tarefa único
        task_id = str(uuid.uuid4())
        print(f"Tarefa recebida e autenticada: user_id={request.user_id}, task_id={task_id}")

        # Seleciona o próximo worker via Round Robin
        worker_addr = self.get_next_worker()
        print(f"Tarefa [{task_id}] atribuída ao worker [{worker_addr}] via Round Robin.")

        # Adiciona a tarefa ao dicionário running_tasks
        self.state.running_tasks[task_id] = {
            "worker_id": worker_addr,
            "status": "EM_EXECUCAO"
        }
        # Persiste o estado
        self.state.save_checkpoint()

        # Retorna resposta
        return tarefas_pb2.TaskResponse(
            task_id=task_id,
            status="RECEBIDA",
            message="Tarefa recebida com sucesso."
        )

    def CheckTaskStatus(self, request, context):
        task_id = request.task_id
        task_info = self.state.running_tasks.get(task_id)
        if task_info:
            return tarefas_pb2.StatusResponse(
                task_id=task_id,
                status=task_info.get("status", "EM_EXECUCAO"),
                message=f"Tarefa {task_id} está com status: {task_info.get('status', 'EM_EXECUCAO')}"
            )
        else:
            context.abort(grpc.StatusCode.NOT_FOUND, f"Tarefa {task_id} não encontrada.")
            # Opcionalmente, pode retornar:
            # return tarefas_pb2.StatusResponse(
            #     task_id=task_id,
            #     status="NAO_ENCONTRADA",
            #     message=f"Tarefa {task_id} não encontrada."
            # )

class WorkerService(tarefas_pb2_grpc.WorkerServiceServicer):
    def __init__(self, state):
        self.state = state

    def SendHeartbeat(self, request, context):
        worker_id = request.worker_id
        self.state.worker_heartbeats[worker_id] = time.time()
        print(f"Heartbeat recebido de {worker_id} em {self.state.worker_heartbeats[worker_id]}")
        return tarefas_pb2.HeartbeatResponse()
