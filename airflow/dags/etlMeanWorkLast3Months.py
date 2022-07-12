import datetime
from io import BytesIO
import pandas as pd
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.models import Variable
from minio import Minio

DEFAULT_ARGS = {
    'owner': 'Airflow',
    'depends_on_past': False,
    'start_date': datetime.datetime(2022, 1, 13),
}

dag = DAG('etlMeanWorkLast3Months', 
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
    
    # faz o download de cada arquivo
    print("Downloading file...")
    
    client.fget_object(
        "processing",
        "employeesDataset.parquet",
        "/tmp/temp_.parquet",
    )

    df = pd.read_parquet("/tmp/temp_.parquet")
    # persiste os arquivos na área de Staging.
    df.to_csv( "/tmp/meanWorkLast3Months.csv"
                ,index=False
            )
 
def transform():

    #ler os dados a partir da área de Staging.
    mean_work_last_3_months = pd.read_csv( "/tmp/meanWorkLast3Months.csv")
    dfLateLast30Absences = mean_work_last_3_months[['EmpID', 'DaysLateLast30', 'Absences']]
    #persiste os dados transformados na área de staging.
    dfLateLast30Absences.to_csv(
        "/tmp/meanWorkLast3Months.csv"
        ,index=False
    )

def load():
    
    #carrega os dados a partir da área de staging.
    df_ = pd.read_csv("/tmp/meanWorkLast3Months.csv")

    #converte os dados para o formato parquet.
    df_.to_parquet(
        "/tmp/meanWorkLast3Months.parquet"
        ,index=False
    )

    #carrega os dados para o Data Lake.
    client.fput_object(
        "processing",
        "meanWorkLast3Months.parquet",
        "/tmp/meanWorkLast3Months.parquet"
    )


extract_task = PythonOperator(
    task_id='extractFileFromDataLake',
    provide_context=True,
    python_callable=extract,
    dag=dag
)

transform_task = PythonOperator(
    task_id='transformData',
    provide_context=True,
    python_callable=transform,
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

extract_task >> transform_task >> load_task >> clean_task