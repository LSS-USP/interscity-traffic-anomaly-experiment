# InterSCity Traffic Anomaly Experiment

## Info about scripts

The `train_model.py` script gather data from platform data-collector,
trains a M.A.D model and store it in a hdfs node. The `anomaly_detection.py`
script expect for further outliers and is feed by the model trained. To run
scripts you should have a functional Spark 2.3.0 build (or use our
docker-compose!) and the python packages listed
in `requirements` file.

## Running (using docker)

Obs: To enter in a container (ie: master), run:
```
$docker exec -it master /bin/bash
```

1. Inside `spark_scripts` folder, run docker containers:
```
$ docker-compose up -d
```

2. Check their status:
```
$ docker-compose ps
```

3. To train the model, run inside the master container:
```
$ train_model
```

4. To detect anomalies you must:
(a) Run `kafka_to_rabbitmq` script: 
```
$ python3 kafka_to_rabbitmq.py
```

(b) Run `rabbitmq_to_kafka` script:
```
$ python3 rabbitmq_to_kafka.py
```

(c) Inside the master container, run `detect_anomaly` script:
```
$ detect_anomalies
```

## Passing data from Rabbitmq to Kafka

The file 'rabbitmq_to_kafka.py` publishes data posted in RabbitMQ by the
platform in a Kafka topic to be consumed by Spark.
Inside this folder, run
```
python3.6 rabbitmq_to_kafka.py
```

## Running Tests

Inside the `tests` folder, run
```
python3.6 -m pytest  anomaly_detection_test.py
```

## Contact

We are always in #interscity @freenode (IRC). Also, feel free to mail us at
`interscity-platform@googlegroups.com`
