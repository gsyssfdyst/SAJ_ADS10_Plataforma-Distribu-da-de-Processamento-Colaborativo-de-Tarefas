import grpc
from concurrent import futures
import threading
import time

from protos import tarefas_pb2_grpc
from orquestrador_backup.servicos_backup import (
    BackupTaskOrchestratorService,
    BackupWorkerService,
    SynchronizationServiceImpl
)
# Importa as classes de serviço principal para failover
from orquestrador.servicos import TaskOrchestratorService, WorkerService

# Variável global para armazenar o último heartbeat do principal
from orquestrador_backup.servicos_backup import last_primary_heartbeat

def monitor_workers(state, check_interval=10, heartbeat_timeout=30):
    while True:
        now = time.time()
        failed_workers = []
        for worker_id, last_heartbeat in list(state.worker_heartbeats.items()):
            if now - last_heartbeat > heartbeat_timeout:
                failed_workers.append(worker_id)
        for failed_worker in failed_workers:
            print(f"[BACKUP] Worker [{failed_worker}] considerado falho.")
            if failed_worker in state.workers:
                state.workers.remove(failed_worker)
            for task_id, task_info in list(state.running_tasks.items()):
                if task_info["worker_id"] == failed_worker:
                    if state.workers:
                        new_worker = state.workers[0]
                        state.running_tasks[task_id]["worker_id"] = new_worker
                        print(f"[BACKUP] Reatribuindo tarefa [{task_id}] para o worker [{new_worker}].")
                        state.save_checkpoint()
                    else:
                        print(f"[BACKUP] Nenhum worker disponível para reatribuir a tarefa [{task_id}].")
            del state.worker_heartbeats[failed_worker]
        time.sleep(check_interval)

def monitor_primary_orchestrator(server, state, heartbeat_timeout=25, check_interval=10):
    import threading
    global last_primary_heartbeat
    while True:
        time.sleep(check_interval)
        now = time.time()
        # Se nunca recebeu heartbeat, continua aguardando
        if last_primary_heartbeat is None:
            continue
        # Se passou do timeout, aciona failover
        if now - last_primary_heartbeat > heartbeat_timeout:
            print("!!!! FALHA DETECTADA NO ORQUESTRADOR PRINCIPAL. ASSUMINDO CONTROLE !!!!")
            # Registra os serviços principais no servidor já existente
            tarefas_pb2_grpc.add_TaskOrchestratorServicer_to_server(TaskOrchestratorService(), server)
            tarefas_pb2_grpc.add_WorkerServiceServicer_to_server(WorkerService(state), server)
            print("Backup promovido a principal. Serviços de orquestração ativados.")
            break  # Para o loop de monitoramento

def serve():
    state = BackupState()
    state.load_from_checkpoint()

    monitor_thread = threading.Thread(target=monitor_workers, args=(state,), daemon=True)
    monitor_thread.start()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tarefas_pb2_grpc.add_SynchronizationServiceServicer_to_server(SynchronizationServiceImpl(state), server)
    server.add_insecure_port('[::]:50052')
    print("[BACKUP] Servidor gRPC escutando na porta 50052...")

    # Inicia monitoramento do principal em thread separada
    failover_thread = threading.Thread(target=monitor_primary_orchestrator, args=(server, state), daemon=True)
    failover_thread.start()

    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
