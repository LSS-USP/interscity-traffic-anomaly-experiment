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
import sys


MAD_CONSTANT = 1.4826
DEFAULT_DATA_COLLECTOR_URL = "http://data-collector:3000"


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
    dom = minidom.parse("/scripts/map_reduced.xml")\
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


def getTickDiff(edge):
    fromTick = int(edge[0][0])
    toTick = int(edge[1][0])
    return (toTick - fromTick)


if __name__ == '__main__':
    data_collector_url = DEFAULT_DATA_COLLECTOR_URL

    if (len(sys.argv) > 1):
        data_collector_url = sys.argv[1]

    spark = SparkSession.builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

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
        val = edges.get((fromId, toId), None)
        if (val == None):
            return -1
        else:
            return val[1]

    udfEdgesUnified = udf(takeBy2, ArrayType(ArrayType(ArrayType(StringType()))))
    udfGetEdge = udf(takeEdge, ArrayType(ArrayType(DoubleType())))
    udfValueMinusMean = udf(valueMinusMean, ArrayType(DoubleType()))
    udfGetEdgeId = udf(getEdgeId, IntegerType())
    udfGetEdgeLength = udf(getEdgeLength, DoubleType())
    udfGetTickDiff = udf(getTickDiff, IntegerType())
    udfMedian = func.udf(median, FloatType())


    # get data from collector
    try:
        r = requests.post(data_collector_url + '/resources/data', json={"capabilities": ["current_location"]})
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
                .where(col("length") != -1)\
                .withColumn("tickDiff", udfGetTickDiff(col("edge")))\
                .where(col("tickDiff") > 0)

        edges_data.show(truncate=False)

        grouped_df = edges_data\
                .withColumn("kmh", col("length") / col("tickDiff"))\
                .groupBy("edgeId")\

        velocity_data = calculatesMad(grouped_df, "kmh")\
                .withColumn("upper_threshold", col("median(kmh)") + 3.*col("mad"))\
                .withColumn("lower_threshold", col("median(kmh)") - 3.*col("mad"))
        velocity_data.show()

        file_path = "hdfs://hadoop:9000/traffic_model.csv"
        velocity_data\
                .select("mad", "upper_threshold", "lower_threshold", "edgeId")\
                .write.mode('overwrite')\
                .option("header", "true")\
                .format("csv")\
                .save(file_path)

        print("Model generation completed! You can find it at %s" % (file_path))

    except:
        raise Exception("""
            Your data_collector looks weird.
            Usage: `train_model ${data_collector_url}`
            (default data_collector_url: http://data_collector:3000)
        """)
