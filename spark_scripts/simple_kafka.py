from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, udf, get_json_object, array, collect_list
from pyspark.sql.types import *
import json


spark = SparkSession.builder.getOrCreate()
spark.sparkContext.setLogLevel("ERROR")


def build_kafka_stream(topic):
    return (spark
            .readStream.format('kafka')
            .option('kafka.bootstrap.servers', 'kafka:9092')
            .option('subscribe', topic)
            .option('failOnDataLoss', False)
            .load()
            .selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)"))


if __name__ == '__main__':
    stream = build_kafka_stream('data_stream')

    (stream
            .writeStream
            .format("console")
            .start())
