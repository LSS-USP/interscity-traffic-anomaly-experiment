# encoding=utf8
import os
import sys

from pyspark.sql.types import *
from math import sin, cos, sqrt, atan2, radians
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, hour, dayofyear, minute, array, udf, collect_list, explode, mean, get_json_object, from_json, size
from pyspark.sql.types import *
from datetime import datetime
from xml.dom import minidom
import requests
from pyspark.sql.window import Window
import json
import builtins
from pyspark.sql import DataFrameStatFunctions as statFunc
import numpy as np
import pyspark.sql.functions as func


MAD_CONSTANT = 1.4826
spark = SparkSession.builder.getOrCreate()
spark.sparkContext.setLogLevel("ERROR")


def takeBy2(points):
    """
    Example:
    >>> takeBy2([1, 2, 3, 4, 5, 6])
    [(1,2),(2,3),(3,4),(4,5),(5,6)] 
    """
    if (len(points) == 1):
        return list(zip(points, points))
    if (len(points) < 1):
        return []

    a1 = points
    a2 = list(points)

    a1.pop()
    a2.pop(0)
    return list(zip(a1, a2))


def takeEdge(item):
    _, lat1, lon1 = item[0]
    _, lat2, lon2 = item[1]
    return [[float(lat1), float(lon1)], [float(lat2), float(lon2)]]


def valueMinusMean(values, mean_val):
    # OBS: enumerate does not reset if it is calld multiple times
    for i, u in enumerate(values):
        values[i] = abs(u - mean_val)
    return values


def getSchema():
    return StructType([
        StructField("uuid", StringType(), False),
        StructField("capabilities", StructType([
            StructField("current_location", ArrayType(
                StructType([
                    StructField("lat", DoubleType(), False),
                    StructField("lon", DoubleType(), False),
                    StructField("date", StringType(), False),
                    StructField("nodeID", DoubleType(), False),
                    StructField("tick", StringType(), False)
                ])
            ))
        ]))
    ])


def loadEdges():
    dom = minidom.parse("map_reduced.xml")\
            .getElementsByTagName('link')
    mylist = []
    for u in dom:
        mylist.append([
            int(u.getAttribute('id')),
            int(u.getAttribute('from')),
            int(u.getAttribute('to')),
            float(u.getAttribute('length'))
        ])
    return mylist


def median(values_list):
    med = np.median(values_list)
    return float(med)


def buildKafkaStream(topics):
    return spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "kafka:9092") \
            .option("subscribe", topics) \
            .option("checkpointLocation", "hdfs://hadoop:9000/")\
            .load() \
            .selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")


def extractJsonFromString(df, attrs):
    json_objects = []
    for u in attrs:
        json_objects.append(get_json_object(df.value, '$.'+u).alias(u))
    return json_objects


def debugStream(stream, outputMode="complete"):
    return stream\
            .writeStream.format("console")\
            .trigger(processingTime='10 seconds')\
            .outputMode(outputMode)\
            .option("truncate", False)\
            .start()\


def calculatesMad(df, c):
    return df\
        .agg(udfMedian(func.collect_list(col(c))).alias("median({0})".format(c)), mean(col(c)), collect_list(col(c)).alias("array({0})".format(c)))\
        .withColumn(
            "{0}-median({0})".format(c), udfValueMinusMean(
                col("array({0})".format(c)), col("median({0})".format(c))
            )
        )\
        .withColumn(
            "median({0}-median({0}))".format(c),
            udfMedian(col("{0}-median({0})".format(c)))
        )\
        .withColumn("mad", col("median({0}-median({0}))".format(c)) * MAD_CONSTANT)

udfMedian = func.udf(median, FloatType())
udfValueMinusMean = udf(valueMinusMean, ArrayType(DoubleType()))

if __name__ == '__main__':
    edges = {}
    for u in loadEdges():
        edges[(u[1], u[2])] = [u[0], u[3]]

    def getEdgeId(edge):
        fromId = int(edge[0][1])
        toId = int(edge[1][1])
        val = edges.get((fromId, toId), None)
        if (val == None):
            return -1
        else:
            return val[0]

    def getEdgeLength(edge):
        fromId = int(edge[0][1])
        toId = int(edge[1][1])
        return edges[(fromId, toId)][1]

    def getTickDiff(edge):
        fromTick = int(edge[0][0])
        toTick = int(edge[1][0])
        return (toTick - fromTick)

    udfEdgesUnified = udf(takeBy2, ArrayType(ArrayType(ArrayType(StringType()))))
    udfGetEdge = udf(takeEdge, ArrayType(ArrayType(DoubleType())))
    udfGetEdgeId = udf(getEdgeId, IntegerType())
    udfGetEdgeLength = udf(getEdgeLength, DoubleType())
    udfGetTickDiff = udf(getTickDiff, IntegerType())

    # get data from collector
    collector_url = "http://data-collector:3000"
    r = requests.post(collector_url + '/resources/data', json={"capabilities": ["current_location"]})
    resources = r.json()["resources"]
    rdd = spark.sparkContext.parallelize(resources)
    df = spark.createDataFrame(resources, getSchema())

    # cleanning the data and calculating mad
    clean_data = df\
            .select("uuid", explode(col("capabilities.current_location")).alias("values"))\
            .withColumn("nodeID", col("values.nodeID").cast(IntegerType()))\
            .select("uuid", "values.date", "nodeID", col("values.tick").cast(IntegerType()), "values.lat", "values.lon")\
            .orderBy("tick", ascending=True)\
            .withColumn("tick+nodeID", array(col("tick"), col("nodeID")))\
            .select("uuid", "tick", "nodeID", "tick+nodeID")

    clean_data.show()

    edges_data = clean_data\
            .groupBy("uuid")\
            .agg(collect_list(col("tick+nodeID")).alias("array(tick+nodeID)"))\
            .select("uuid", udfEdgesUnified(col("array(tick+nodeID)")).alias("edges"))\
            .select(explode(col("edges")).alias("edge"), "uuid")\
            .withColumn("edgeId", udfGetEdgeId(col("edge")))\
            .where(col("edgeId") != -1)\
            .withColumn("length", udfGetEdgeLength(col("edge")))\
            .withColumn("tickDiff", udfGetTickDiff(col("edge")))\
            .where(col("tickDiff") > 0)

    edges_data.show(truncate=False)

    grouped_df = edges_data\
            .withColumn("kmh", col("length") / col("tickDiff"))\
            .groupBy("edgeId")\

    velocity_data = calculatesMad(grouped_df, "kmh")\
            .withColumn("upper_threshold", col("median(kmh)") + 3.*col("mad"))\
            .withColumn("lower_threshold", col("median(kmh)") - 3.*col("mad"))

    velocity_data.select("mad", "upper_threshold", "lower_threshold").show(truncate=False)

    thresholds = {}

    annon = velocity_data.select("upper_threshold", "lower_threshold", "edgeId").rdd.collect()
    for u in annon:
        thresholds[u["edgeId"]] = [u["lower_threshold"], u["upper_threshold"]]


    def compareValues(edgeId, kmh):
        lower, upper = thresholds.get(edgeId)
        return (kmh > upper) or (kmh < lower)


    udfIsAnomaly = udf(compareValues, BooleanType())

    df = buildKafkaStream("data_stream")

    stream = df\
            .select(extractJsonFromString(df, ["tick", "nodeID", "uuid"]))\
            .withColumn("merged", array(col("tick"), col("nodeID")))\
            .groupBy("uuid")\
            .agg(collect_list(col("merged")).alias("tick+nodeID"))\
            .select("uuid", udfEdgesUnified(col("tick+nodeID")).alias("edges"))\
            .select(explode(col("edges")).alias("edge"), "uuid")\
            .filter(size(col("edge")) >= 2)\
            .withColumn("edgeId", udfGetEdgeId(col("edge")))\
            .where(col("edgeId") != -1)\
            .withColumn("length", udfGetEdgeLength(col("edge")))\
            .withColumn("tickDiff", udfGetTickDiff(col("edge")))\
            .withColumn("kmh", col("length") / col("tickDiff"))\
            .withColumn("is_anomaly", udfIsAnomaly(col("edgeId"), col("kmh")))

    debugStream(stream).awaitTermination()
