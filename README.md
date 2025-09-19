
# Plataforma Distribuída de Processamento Colaborativo de Tarefas

## Visão Geral

Este projeto, desenvolvido para a disciplina de Sistemas Distribuídos do IFBA - Campus Santo Antônio de Jesus, implementa uma plataforma de orquestração de tarefas que simula um sistema real de processamento colaborativo.

A plataforma permite que clientes submetam trabalhos, que são distribuídos para múltiplos nós de processamento (workers) de forma balanceada. O sistema é tolerante a falhas, garantindo a reatribuição de tarefas e a continuidade da operação mesmo com a queda do coordenador principal, através de um mecanismo de failover para um orquestrador de backup.

## Funcionalidades Principais

* **Orquestração de Tarefas:** Um coordenador principal gerencia o ciclo de vida das tarefas.
* **Balanceamento de Carga:** As tarefas são distribuídas entre os workers ativos usando uma política Round Robin.
* **Tolerância a Falhas:**
    * **Failover de Orquestrador:** Um orquestrador de backup assume o controle se o principal falhar.
    * **Reatribuição de Tarefas:** Tarefas em execução em workers que falham são redistribuídas para outros nós ativos.
* **Comunicação via gRPC:** A comunicação entre todos os componentes é feita utilizando o framework gRPC para alta performance.
* **Autenticação de Cliente:** A submissão de tarefas requer autenticação básica por token.

## Estrutura do Projeto

```

/
|-- projeto\_distribuido/
|   |-- orquestrador/       \# Lógica do Coordenador Principal
|   |-- protos/             \# Arquivos .proto e código gRPC gerado
|   |-- **init**.py
|   ` -- requirements.txt |-- orquestrador-backup/    # Lógica do Coordenador de Backup |-- worker/                 # Lógica dos Nós de Processamento |-- cliente/                # Lógica do Cliente para interação  `-- README.md

````

## Guia de Execução

Siga os passos abaixo para configurar o ambiente e executar a plataforma completa.

### 1. Pré-requisitos

* Python 3.8 ou superior
* `pip` e `venv`

### 2. Configuração do Ambiente

Execute os seguintes comandos no terminal, a partir da pasta raiz do projeto.

**a. Crie e Ative um Ambiente Virtual:**
```bash
python -m venv .venv
source .venv/bin/activate
````

**b. Instale as Dependências:**

```bash
pip install -r projeto_distribuido/requirements.txt
```

**c. Gere o Código gRPC:**
Este comando é **essencial** e compila o arquivo `.proto`, criando os módulos Python necessários para a comunicação entre os serviços.

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. ./projeto_distribuido/protos/tarefas.proto
```

### 3\. Executando a Plataforma

Para rodar o sistema, você precisará de **múltiplos terminais abertos** (pelo menos 6), um para cada componente. A ordem de inicialização é importante.

**Terminal 1 - Orquestrador Principal:**

```bash
python -m projeto_distribuido.orquestrador.main
```

*(Você verá a mensagem `Orquestrador Principal iniciado na porta 50051...` e avisos de que o backup não está disponível. Isso é esperado.)*

**Terminal 2 - Orquestrador Backup:**
*O comando `export PYTHONPATH` permite que o Python encontre os outros pacotes do projeto.*

```bash
export PYTHONPATH=$PYTHONPATH:.
python -m orquestrador-backup.main_backup
```

*(Você verá a mensagem `Orquestrador Backup iniciado na porta 50052...`. No Terminal 1, os avisos de erro devem parar.)*

**Terminal 3 - Worker 1:**

```bash
export PYTHONPATH=$PYTHONPATH:.
python -m worker.main_worker --port 50061
```

**Terminal 4 - Worker 2:**

```bash
export PYTHONPATH=$PYTHONPATH:.
python -m worker.main_worker --port 50062
```

**Terminal 5 - Worker 3:**

```bash
export PYTHONPATH=$PYTHONPATH:.
python -m worker.main_worker --port 50063
```

*(Neste ponto, toda a infraestrutura está no ar e os workers estão enviando heartbeats.)*

**Terminal 6 - Cliente:**

```bash
export PYTHONPATH=$PYTHONPATH:.
python -m cliente.main_cliente
```

*Um menu interativo aparecerá. Use as seguintes credenciais para testar:*

  * **user\_id:** `user1`
  * **user\_token:** `token_valido_123`

-----

## Como Simular e Demonstrar as Falhas

Testar a tolerância a falhas é um requisito central deste projeto. Siga os cenários abaixo para gerar evidências para o seu relatório.

### Cenário 1: Falha de um Worker e Reatribuição de Tarefa

**Objetivo:** Mostrar que o Orquestrador detecta a queda de um worker e move a tarefa que estava com ele para um worker saudável.

1.  **Submeta uma Tarefa:** No Cliente (Terminal 6), submeta uma tarefa.
2.  **Observe a Atribuição:** No Orquestrador (Terminal 1), veja qual worker recebeu a tarefa (ex: `Tarefa [...] atribuída ao worker [localhost:50062]`).
3.  **Derrube o Worker:** Vá para o terminal do worker que recebeu a tarefa (neste exemplo, Terminal 4) e pressione `Ctrl + C` para encerrar o processo.
4.  **Observe a Detecção:** No Orquestrador (Terminal 1), aguarde alguns segundos. Você verá a mensagem: `Worker [localhost:50062] considerado falho.`
5.  **Observe a Reatribuição:** Imediatamente após, o orquestrador reatribuirá a tarefa. Você verá um log como: `Reatribuindo tarefa [...] para o worker [outro_worker_ativo].`
6.  **Verifique no Cliente:** Use a opção 2 no cliente para verificar o status da tarefa. Ela continuará sendo processada, provando que o sistema se recuperou.

### Cenário 2: Falha do Orquestrador Principal (Failover)

**Objetivo:** Mostrar que o Orquestrador Backup assume o controle total quando o principal falha.

1.  **Submeta uma Tarefa:** Use o cliente para garantir que o sistema está em operação.
2.  **Derrube o Orquestrador Principal:** Vá para o Terminal 1 e pressione `Ctrl + C`.
3.  **Observe o Failover:** No Orquestrador Backup (Terminal 2), aguarde alguns segundos. Você verá a mensagem de alerta:
    `!!!! FALHA NO PRINCIPAL DETECTADA. ASSUMINDO CONTROLE !!!!`
    Seguida de: `Backup promovido a principal.`
4.  **Teste o Novo Principal:** No Cliente (Terminal 6), submeta uma **nova tarefa**. O cliente (já configurado para tentar se conectar à porta 50052 se a 50051 falhar) deverá submeter a tarefa com sucesso.
5.  **Observe o Log do Backup:** No Terminal 2, você verá os logs de recebimento e atribuição da nova tarefa, provando que ele assumiu completamente o papel de coordenador.

<!-- end list -->

```
```