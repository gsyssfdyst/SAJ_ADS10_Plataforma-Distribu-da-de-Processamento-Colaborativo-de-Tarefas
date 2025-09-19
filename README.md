# Plataforma Distribuída de Processamento Colaborativo de Tarefas

Este projeto, desenvolvido para a disciplina de Sistemas Distribuídos, implementa uma plataforma de orquestração de tarefas que simula um sistema real de processamento colaborativo. A plataforma permite que clientes submetam trabalhos, que são distribuídos para múltiplos nós de processamento (workers) de forma balanceada. O sistema é tolerante a falhas, garantindo a reatribuição de tarefas e a continuidade da operação mesmo com a queda do coordenador principal.

Estrutura do Projeto

# O sistema é dividido em quatro componentes principais:

    Orquestrador Principal (projeto_distribuido/orquestrador): O cérebro do sistema. Recebe tarefas dos clientes, distribui para os workers usando uma política Round Robin, monitora a saúde dos workers e sincroniza seu estado com o backup.

    Orquestrador Backup (orquestrador-backup): Uma cópia de prontidão do orquestrador principal. Recebe atualizações de estado e assume o controle (failover) caso o principal falhe.

    Workers (worker): Os nós de processamento. Executam as tarefas que recebem do orquestrador, enviam sinais de vida (heartbeats) e podem falhar de forma simulada para testar a resiliência do sistema.

    Cliente (cliente): A interface de linha de comando que permite aos usuários submeterem tarefas autenticadas e consultarem o status de seus trabalhos.

Guia de Execução

Siga os passos abaixo para configurar o ambiente e executar a plataforma completa.

1. Pré-requisitos

    Python 3.8 ou superior

    pip (gerenciador de pacotes do Python)

2. Configuração do Ambiente

Execute os seguintes comandos no terminal, a partir da pasta raiz do projeto.

a. Crie e Ative um Ambiente Virtual (Recomendado):
Bash

python -m venv .venv
source .venv/bin/activate

b. Instale as Dependências:
Bash

pip install -r projeto_distribuido/requirements.txt

c. Gere o Código gRPC:
Este comando compila o arquivo .proto e cria os arquivos Python necessários para a comunicação entre os serviços.
Bash

python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. ./projeto_distribuido/protos/tarefas.proto

3. Executando a Plataforma

Para rodar o sistema, você precisará de múltiplos terminais abertos (pelo menos 6), um para cada componente. A ordem de inicialização é importante.

Terminal 1 - Orquestrador Principal:
Bash

python -m projeto_distribuido.orquestrador.main

Você verá a mensagem Orquestrador Principal iniciado na porta 50051... e alguns avisos de que o backup não está disponível. Isso é normal.

Terminal 2 - Orquestrador Backup:
Este comando adiciona o diretório atual ao PYTHONPATH, permitindo que o Python encontre os outros pacotes do projeto.
Bash

export PYTHONPATH=$PYTHONPATH:.
python -m orquestrador-backup.main_backup

Você verá a mensagem Orquestrador Backup iniciado na porta 50052.... No Terminal 1, os avisos de erro devem parar.

Terminal 3 - Worker 1:
Bash

export PYTHONPATH=$PYTHONPATH:.
python -m worker.main_worker --port 50061

Você verá o worker iniciar e começar a enviar heartbeats.

Terminal 4 - Worker 2:
Bash

export PYTHONPATH=$PYTHONPATH:.
python -m worker.main_worker --port 50062

Terminal 5 - Worker 3:
Bash

export PYTHONPATH=$PYTHONPATH:.
python -m worker.main_worker --port 50063

Neste ponto, toda a infraestrutura está no ar.

Terminal 6 - Cliente:
Bash

export PYTHONPATH=$PYTHONPATH:.
python -m cliente.main_cliente

Um menu interativo aparecerá. Use as seguintes credenciais para testar:

    user_id: user1

    user_token: token_valido_123

Como Simular e Demonstrar as Falhas

Testar a tolerância a falhas é um requisito central deste projeto. Siga os cenários abaixo para gerar evidências para o seu relatório.

Cenário 1: Falha de um Worker e Reatribuição de Tarefa

Objetivo: Mostrar que o Orquestrador detecta a queda de um worker e move a tarefa que estava com ele para um worker saudável.

    Submeta uma Tarefa: No Cliente (Terminal 6), submeta uma tarefa.

    Observe a Atribuição: No Orquestrador (Terminal 1), veja qual worker recebeu a tarefa (ex: Tarefa [...] atribuída ao worker [localhost:50062]).

    Derrube o Worker: Vá para o terminal do worker que recebeu a tarefa (neste exemplo, Terminal 4) e pressione Ctrl + C para encerrar o processo.

    Observe a Detecção: No Orquestrador (Terminal 1), aguarde alguns segundos. Você verá a mensagem: Worker [localhost:50062] considerado falho.

    Observe a Reatribuição: Imediatamente após, o orquestrador reatribuirá a tarefa. Você verá um log como: Reatribuindo tarefa [...] para o worker [outro_worker_ativo].

    Verifique no Cliente: Use a opção 2 no cliente para verificar o status da tarefa. Ela continuará sendo processada, provando que o sistema se recuperou.

Cenário 2: Falha do Orquestrador Principal (Failover)

Objetivo: Mostrar que o Orquestrador Backup assume o controle total quando o principal falha.

    Submeta uma Tarefa: Use o cliente para garantir que o sistema está em operação.

    Derrube o Orquestrador Principal: Vá para o Terminal 1 e pressione Ctrl + C.

    Observe o Failover: No Orquestrador Backup (Terminal 2), aguarde alguns segundos. Você verá a mensagem de alerta:
    !!!! FALHA NO PRINCIPAL DETECTADA. ASSUMINDO CONTROLE !!!!
    Seguida de: Backup promovido a principal.

    Teste o Novo Principal: No Cliente (Terminal 6), submeta uma nova tarefa. O cliente (já configurado para tentar se conectar à porta 50052 se a 50051 falhar) deverá submeter a tarefa com sucesso.

    Observe o Log do Backup: No Terminal 2, você verá os logs de recebimento e atribuição da nova tarefa, provando que ele assumiu completamente o papel de coordenador.