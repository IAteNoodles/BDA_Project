FROM postgres:14-alpine
COPY 01-airflow-db.sql /docker-entrypoint-initdb.d/01-airflow-db.sql
COPY init.sql /docker-entrypoint-initdb.d/02-init.sql
COPY seed/ /seed/
RUN chmod -R 755 /seed/ && chmod 644 /seed/*