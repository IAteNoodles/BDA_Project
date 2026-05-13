FROM maven:3.9-eclipse-temurin-11 AS builder

WORKDIR /build

COPY pom.xml .
RUN mvn dependency:go-offline -B

COPY src ./src
RUN mvn clean package -DskipTests -B

FROM bde2020/spark-master:3.0.0-hadoop3.2

COPY --from=builder /build/target/spark-jobs-1.0.0-jar-with-dependencies.jar /opt/spark/jobs/

WORKDIR /opt/spark

COPY <<'EOF' /opt/spark/entrypoint.sh
#!/bin/bash
echo "Spark Jobs container started. Ready to accept spark-submit requests."
echo "Available JAR: /opt/spark/jobs/spark-jobs-1.0.0-jar-with-dependencies.jar"
echo "Spark Master: ${SPARK_MASTER_URL:-spark://spark-master:7077}"
tail -f /dev/null
EOF
RUN chmod +x /opt/spark/entrypoint.sh

ENTRYPOINT ["/opt/spark/entrypoint.sh"]