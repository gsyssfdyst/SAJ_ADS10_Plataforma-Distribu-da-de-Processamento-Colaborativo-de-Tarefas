import grpc
from concurrent import futures
import threading
import time

from protos import tarefas_pb2_grpc
from orquestrador.servicos import TaskOrchestratorService, WorkerService
from orquestrador.estado import GlobalState

def monitor_workers(global_state, check_interval=10, heartbeat_timeout=30):
    while True:
        now = time.time()
        # Detecta workers falhos
        failed_workers = []
        for worker_id, last_heartbeat in list(global_state.worker_heartbeats.items()):
            if now - last_heartbeat > heartbeat_timeout:
                failed_workers.append(worker_id)
        for failed_worker in failed_workers:
            print(f"Worker [{failed_worker}] considerado falho.")
            # Remove da lista de workers ativos
            if failed_worker in global_state.workers:
                global_state.workers.remove(failed_worker)
            # Reatribui tarefas
            for task_id, task_info in list(global_state.running_tasks.items()):
                if task_info["worker_id"] == failed_worker:
                    # Seleciona novo worker ativo
                    if global_state.workers:
                        # Round Robin: pega o próximo worker (simplesmente o primeiro da lista)
                        new_worker = global_state.workers[0]
                        global_state.running_tasks[task_id]["worker_id"] = new_worker
                        print(f"Reatribuindo tarefa [{task_id}] para o worker [{new_worker}].")
                        global_state.save_checkpoint()
                    else:
                        print(f"Nenhum worker disponível para reatribuir a tarefa [{task_id}].")
            # Remove o heartbeat do worker falho
            del global_state.worker_heartbeats[failed_worker]
        time.sleep(check_interval)

def send_heartbeat_to_backup(interval=5):
    from protos import tarefas_pb2_grpc
    from google.protobuf import empty_pb2
    while True:
        try:
            with grpc.insecure_channel('localhost:50052') as channel:
                stub = tarefas_pb2_grpc.SynchronizationServiceStub(channel)
                stub.PrimaryHeartbeat(empty_pb2.Empty())
                print("[SYNC] Heartbeat enviado para o backup.")
        except Exception as e:
            print(f"[SYNC] Erro ao enviar heartbeat para o backup: {e}")
        time.sleep(interval)

def serve():
    # Carrega o estado global do checkpoint
    global_state = GlobalState()
    global_state.load_from_checkpoint()

    # Inicia monitoramento dos workers em thread daemon
    monitor_thread = threading.Thread(target=monitor_workers, args=(global_state,), daemon=True)
    monitor_thread.start()

    # Inicia envio de heartbeat para o backup em thread daemon
    heartbeat_thread = threading.Thread(target=send_heartbeat_to_backup, daemon=True)
    heartbeat_thread.start()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # Instancia o serviço usando o estado carregado
    tarefas_pb2_grpc.add_TaskOrchestratorServicer_to_server(TaskOrchestratorService(), server)
    tarefas_pb2_grpc.add_WorkerServiceServicer_to_server(WorkerService(global_state), server)
    server.add_insecure_port('[::]:50051')
    print("Servidor gRPC escutando na porta 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
