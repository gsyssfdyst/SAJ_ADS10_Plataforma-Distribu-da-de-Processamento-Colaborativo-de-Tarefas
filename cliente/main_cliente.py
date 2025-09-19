import grpc
from protos import tarefas_pb2, tarefas_pb2_grpc

def submit_task(user_id, token, task_details):
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = tarefas_pb2_grpc.TaskOrchestratorStub(channel)
            request = tarefas_pb2.TaskRequest(
                user_id=user_id,
                user_token=token,
                task_details=task_details
            )
            response = stub.SubmitTask(request)
            print(f"Tarefa submetida com sucesso! ID da Tarefa: {response.task_id}")
            print(f"Status: {response.status}")
            print(f"Mensagem: {response.message}")
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            print("Erro de autenticação: usuário ou token inválido.")
        else:
            print(f"Erro ao conectar ao orquestrador: {e.details()}")

def check_status(task_id):
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = tarefas_pb2_grpc.TaskOrchestratorStub(channel)
            request = tarefas_pb2.StatusRequest(task_id=task_id)
            response = stub.CheckTaskStatus(request)
            print(f"Status da Tarefa [{task_id}]: {response.status}")
            print(f"Mensagem: {response.message}")
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            print(f"Tarefa [{task_id}] não encontrada.")
        else:
            print(f"Erro ao consultar status: {e.details()}")

if __name__ == "__main__":
    print("Cliente para interação com o Orquestrador")
    print("1: Submeter Tarefa")
    print("2: Verificar Status de Tarefa")
    escolha = input("Escolha uma opção (1 ou 2): ").strip()
    if escolha == "1":
        user_id = input("Informe seu user_id: ")
        token = input("Informe seu user_token: ")
        task_details = input("Descreva a tarefa: ")
        submit_task(user_id, token, task_details)
    elif escolha == "2":
        task_id = input("Informe o ID da tarefa: ")
        check_status(task_id)
    else:
        print("Opção inválida.")
