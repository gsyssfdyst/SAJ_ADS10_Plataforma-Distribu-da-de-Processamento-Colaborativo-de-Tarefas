import grpc
from concurrent import futures
import threading
import time

from projeto_distribuido.protos import tarefas_pb2_grpc
from projeto_distribuido.orquestrador.servicos import TaskOrchestratorService, WorkerService
from projeto_distribuido.orquestrador.estado import GlobalState

def monitor_workers(global_state, check_interval=10, heartbeat_timeout=30):
    while True:
        time.sleep(check_interval)
        now = time.time()
        failed_workers = [
            worker_id for worker_id, last_heartbeat in global_state.worker_heartbeats.items()
            if now - last_heartbeat > heartbeat_timeout
        ]
        for worker_id in failed_workers:
            print(f"Worker [{worker_id}] considerado falho.")
            if worker_id in global_state.workers:
                global_state.workers.remove(worker_id)
            del global_state.worker_heartbeats[worker_id]
            # Lógica de reatribuição de tarefas aqui, se necessário

def send_heartbeat_to_backup(interval=5):
    from google.protobuf import empty_pb2
    while True:
        try:
            with grpc.insecure_channel('localhost:50052') as channel:
                stub = tarefas_pb2_grpc.SynchronizationServiceStub(channel)
                stub.PrimaryHeartbeat(empty_pb2.Empty())
        except Exception:
            print("[SYNC] Backup não está disponível.")
        time.sleep(interval)

def serve():
    global_state = GlobalState()
    global_state.load_from_checkpoint()

    threading.Thread(target=monitor_workers, args=(global_state,), daemon=True).start()
    threading.Thread(target=send_heartbeat_to_backup, daemon=True).start()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tarefas_pb2_grpc.add_TaskOrchestratorServicer_to_server(TaskOrchestratorService(global_state), server)
    tarefas_pb2_grpc.add_WorkerServiceServicer_to_server(WorkerService(global_state), server)
    
    server.add_insecure_port('[::]:50051')
    print("Orquestrador Principal iniciado na porta 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()