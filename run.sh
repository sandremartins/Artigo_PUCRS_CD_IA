# criar venv
virtualenv -p python3 venv
# ativar venv
source venv/bin/activate
# criar e atualizar requiriments
pip freeze > requirements.txt

# Instalação e Configuração do Mysql Server
docker run --name bdrhengajamento --platform linux/x86_64 --env MYSQL_ROOT_PASSWORD=rhengajamento -p "3307:3306" -d mysql
# listar os containers
docker container ps

# Instalação e Configuração do Data Lake com MinIO Server
# criar repositorio datalake
mkdir datalake
docker run --name miniorhengajamento -d -p 9000:9000 -p 9001:9001 -v "$PWD/datalake:/data" minio/minio server /data --console-address ":9001"
# acessar em http://localhost:9001/login e copiar o ip que se encontra em metrics, 172.17.0.3 pois irá ser utilizado para configurar o airflow


# Instalação e Configuração do Airflow
mkdir airflow
cd airflow 
mkdir dags
cd..
docker run -d -p 8080:8080 -v "$PWD/airflow/dags:/opt/airflow/dags/" --entrypoint=/bin/bash --name airflow apache/airflow:2.1.1-python3.8 -c '(airflow db init && airflow users create --username admin --password rhengajamento --firstname Alessandre --lastname Martins --role Admin --email sandremartins@gmail.com); airflow webserver & airflow scheduler'
#  Instale as bibliotecas necessárias para o ambiente airflow
# conectar no airflow
docker container exec -it airflowrhengajamento bash

pip install pymysql xlrd openpyxl minio

# acessar o airflow via http://localhost:8080/login/
