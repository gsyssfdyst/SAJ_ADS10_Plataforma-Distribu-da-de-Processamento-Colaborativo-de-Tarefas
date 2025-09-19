import time
import random
import os

def execute_task(task_details):
    print(f"[WORKER] Executando tarefa: {task_details}")
    time.sleep(2)  # Simula tempo de execução
    print(f"[WORKER] Tarefa concluída: {task_details}")

def execute_long_running_task(task_id, task_details):
    print(f"Iniciando tarefa [{task_id}]: {task_details}")
    duration = random.randint(5, 15)
    fail_chance = random.random()
    # Simula processamento com possibilidade de falha
    for i in range(duration):
        time.sleep(1)
        if i == duration // 2 and fail_chance < 0.3:
            print(f"ERRO FATAL: Falha simulada durante a execução da tarefa [{task_id}]!")
            os._exit(1)
    print(f"Tarefa [{task_id}] concluída com sucesso.")
    return "CONCLUÍDA"
