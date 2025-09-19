import time
import grpc
import threading
import uuid
import argparse

from protos import tarefas_pb2, tarefas_pb2_grpc
from worker.task_executor import execute_task, execute_long_running_task

def send_heartbeat(worker_id, orchestrator_address, backup_address="localhost:50052"):
    while True:
        sent = False
        for addr in [orchestrator_address, backup_address]:
            try:
                with grpc.insecure_channel(addr) as channel:
                    stub = tarefas_pb2_grpc.WorkerServiceStub(channel)
                    stub.SendHeartbeat(tarefas_pb2.HeartbeatRequest(worker_id=worker_id))
                    print(f"[WORKER] Heartbeat enviado para o orquestrador ({addr}).")
                    sent = True
                    break
            except Exception as e:
                print(f"[WORKER] Erro ao enviar heartbeat para {addr}: {e}")
        if not sent:
            print("[WORKER] Nenhum orquestrador disponível para receber heartbeat.")
        time.sleep(5)

class WorkerNodeServiceImpl(tarefas_pb2_grpc.WorkerNodeServiceServicer):
    def ExecuteTask(self, request, context):
        status = execute_long_running_task(request.task_id, request.task_details)
        return tarefas_pb2.ExecuteTaskResponse(
            task_id=request.task_id,
            status=status
        )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, required=True, help='Porta para escutar o servidor gRPC do worker')
    args = parser.parse_args()
    port = args.port

    worker_id = f"localhost:{port}"
    orchestrator_addr = "localhost:50051"

    print(f"[WORKER] Iniciando worker com ID: {worker_id} na porta {port}")

    server = grpc.server(threading.ThreadPoolExecutor(max_workers=5))
    tarefas_pb2_grpc.add_WorkerNodeServiceServicer_to_server(WorkerNodeServiceImpl(), server)
    server.add_insecure_port(f'[::]:{port}')
    print(f"[WORKER] Servidor gRPC escutando na porta {port}...")
    server.start()

    heartbeat_thread = threading.Thread(
        target=send_heartbeat,
        args=(worker_id, orchestrator_addr),
        daemon=True
    )
    heartbeat_thread.start()

    server.wait_for_termination()

if __name__ == "__main__":
    main()
