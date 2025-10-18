# Passos após clonagem do projeto

## Inicializar o Banco de Dados do Airflow:
O comando abaixo baixa as imagens necessárias para o Airflow funcionar e inicia o banco de dados do Airflow em um container.

`docker-compose up airflow-init`

## Inicializar os serviços do Airflow
O comando abaixo inicia todos os serviços do Airflow (servidor web, agendador, banco de dados).
Os containers criados podem ser vistos no Docker Desktop.

`docker-compose up -d`


Para acessar a interface do Airflow, acesse `[text](http://localhost:8080)`

Será exibido um formulário de login. As credenciais são por padrão:
login: admin
senha: admin

Caso o formulário retorne credenciais incorretas, rode o comando abaixo apra criar um usuário administrador com essas credenciais.

`ocker-compose exec airflow-scheduler airflow users create -r Admin -u admin -e admin@example.com -f admin -l user -p admin`