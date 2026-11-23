# Airflow con los flujos de BolsaLAB adentro, para el clúster local (kind).
# Misma versión que el chart (helm list -n airflow: APP VERSION 3.2.2).
#   docker build -t bolsalab/airflow:dev deploy/airflow
# En EKS los flujos llegarían por git-sync en vez de copiarse en la imagen.
FROM apache/airflow:3.2.2

COPY dags/ /opt/airflow/dags/
