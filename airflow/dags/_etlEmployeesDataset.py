from datetime import datetime,date, timedelta
import pandas as pd
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.models import Variable
from minio import Minio


DEFAULT_ARGS = {
    'owner': 'Airflow',
    'depends_on_past': False,
    'start_date': datetime(2022, 1, 13),
}

dag = DAG('_etlEmployeesDataset', 
          default_args=DEFAULT_ARGS,
          schedule_interval="@once"
        )

data_lake_server = Variable.get("data_lake_server")
data_lake_login = Variable.get("data_lake_login")
data_lake_password = Variable.get("data_lake_password")

client = Minio(
        data_lake_server,
        access_key=data_lake_login,
        secret_key=data_lake_password,
        secure=False
    )

def extract():
    # obter dados do arquivo.
    # cria a estrutura para o dataframe.
    df = pd.DataFrame(data=None)
    
    # busca a lista de objetos no data lake.
    objects = client.list_objects('landing', recursive=True)
    
    # faz o download de cada arquivo e concatena com o dataframe vazio.
    for obj in objects:
        print("Downloading file...")
        print(obj.bucket_name, obj.object_name.encode('utf-8'))

        client.fget_object(
                    obj.bucket_name,
                    obj.object_name.encode('utf-8'),
                    "/tmp/temp_.csv",
        )
        dfTemp = pd.read_csv("/tmp/temp_.csv")
        df = pd.concat([df,dfTemp],axis=1)

    #persiste os arquivos na área de Staging.
    df.to_csv("/tmp/employeesDataset.csv"
               ,index=False
            )

def load():

    #carrega os dados a partir da área de staging.
    df_ = pd.read_csv("/tmp/employeesDataset.csv")

    #converte os dados para o formato parquet.    
    df_.to_parquet(
            "/tmp/employeesDataset.parquet"
            ,index=False
    )

    #carrega os dados para o Data Lake.
    client.fput_object(
        "processing",
        "employeesDataset.parquet",
        "/tmp/employeesDataset.parquet"
    )


extract_task = PythonOperator(
    task_id='extractDataFromDatalake',
    provide_context=True,
    python_callable=extract,
    dag=dag
)

load_task = PythonOperator(
    task_id='loadFileToDataLake',
    provide_context=True,
    python_callable=load,
    dag=dag
)

clean_task = BashOperator(
    task_id="cleanFilesOnStaging",
    bash_command="rm -f /tmp/*.csv;rm -f /tmp/*.json;rm -f /tmp/*.parquet;",
    dag=dag
)

extract_task >> load_task >> clean_task