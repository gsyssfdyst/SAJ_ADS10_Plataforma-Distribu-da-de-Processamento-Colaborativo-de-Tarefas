import grpc
# CORREÇÃO: Usar o caminho absoluto a partir do pacote 'projeto_distribuido'
from projeto_distribuido.protos import tarefas_pb2, tarefas_pb2_grpc

def submit_task(user_id, token, task_details):
    try:
        # Tenta conectar ao principal, se falhar, tenta o backup
        addresses = ['localhost:50051', 'localhost:50052']
        for addr in addresses:
            try:
                with grpc.insecure_channel(addr) as channel:
                    stub = tarefas_pb2_grpc.TaskOrchestratorStub(channel)
                    request = tarefas_pb2.TaskRequest(
                        user_id=user_id,
                        user_token=token,
                        task_details=task_details
                    )
                    response = stub.SubmitTask(request, timeout=5)
                    print(f"Tarefa submetida com sucesso! ID da Tarefa: {response.task_id}")
                    print(f"Status: {response.status}")
                    return
            except grpc.RpcError:
                print(f"Não foi possível conectar ao orquestrador em {addr}. Tentando próximo...")
        print("Erro: Nenhum orquestrador disponível.")

    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

def check_status(task_id):
    try:
        addresses = ['localhost:50051', 'localhost:50052']
        for addr in addresses:
            try:
                with grpc.insecure_channel(addr) as channel:
                    stub = tarefas_pb2_grpc.TaskOrchestratorStub(channel)
                    request = tarefas_pb2.StatusRequest(task_id=task_id)
                    response = stub.CheckTaskStatus(request, timeout=5)
                    print(f"Status da Tarefa [{task_id}]: {response.status}")
                    return
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.NOT_FOUND:
                    print(f"Tarefa [{task_id}] não encontrada.")
                    return
                else:
                    print(f"Não foi possível conectar ao orquestrador em {addr}. Tentando próximo...")
        print("Erro: Nenhum orquestrador disponível.")

    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    while True:
        print("\n--- Cliente para Interação com o Orquestrador ---")
        print("1: Submeter Tarefa")
        print("2: Verificar Status de Tarefa")
        print("3: Sair")
        escolha = input("Escolha uma opção: ").strip()

        if escolha == "1":
            user_id = input("Informe seu user_id: ")
            token = input("Informe seu user_token: ")
            task_details = input("Descreva a tarefa: ")
            submit_task(user_id, token, task_details)
        elif escolha == "2":
            task_id = input("Informe o ID da tarefa: ")
            check_status(task_id)
        elif escolha == "3":
            print("Saindo...")
            break
        else:
            print("Opção inválida.")
