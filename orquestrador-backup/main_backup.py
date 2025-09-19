import grpc
from concurrent import futures
import threading
import time

from projeto_distribuido.protos import tarefas_pb2_grpc
from projeto_distribuido.orquestrador.servicos import TaskOrchestratorService, WorkerService
from .servicos_backup import SynchronizationServiceImpl, last_primary_heartbeat_time
from .estado_backup import BackupState

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
            if failed_worker in state.worker_heartbeats:
                del state.worker_heartbeats[failed_worker]
        time.sleep(check_interval)

def monitor_primary_orchestrator(server, state, heartbeat_timeout=25):
    while True:
        time.sleep(5)
        if last_primary_heartbeat_time.get('time') is None:
            continue
        if time.time() - last_primary_heartbeat_time['time'] > heartbeat_timeout:
            print("!!!! FALHA NO PRINCIPAL DETECTADA. ASSUMINDO CONTROLE !!!!")
            tarefas_pb2_grpc.add_TaskOrchestratorServicer_to_server(TaskOrchestratorService(state), server)
            tarefas_pb2_grpc.add_WorkerServiceServicer_to_server(WorkerService(state), server)
            print("Backup promovido a principal.")
            break

def serve():
    state = BackupState()
    state.load_from_checkpoint()
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tarefas_pb2_grpc.add_SynchronizationServiceServicer_to_server(SynchronizationServiceImpl(state), server)
    
    threading.Thread(target=monitor_primary_orchestrator, args=(server, state), daemon=True).start()
    
    server.add_insecure_port('[::]:50052')
    print("Orquestrador Backup iniciado na porta 50052...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
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
