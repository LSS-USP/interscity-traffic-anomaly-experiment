# encoding=utf8
import os
import sys

from round_coordinates import load_nodes_from_xml, load_edges_from_xml
from math import sin, cos, sqrt, atan2, radians
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, hour, dayofyear, minute, array, udf, collect_list, explode, mean
from pyspark.sql.types import *
from datetime import datetime


def minute_mod10(minute):
    return minute % 10


def getDistanceFromLatLonInKm(lat1,lon1,lat2,lon2):
    R = 6371 # Radius of the earth in km
    dLat = radians(lat2-lat1)
    dLon = radians(lon2-lon1)
    rLat1 = radians(lat1)
    rLat2 = radians(lat2)
    a = sin(dLat/2) * sin(dLat/2) + cos(rLat1) * cos(rLat2) * sin(dLon/2) * sin(dLon/2) 
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    d = R * c # Distance in km
    return d


def calc_velocity(dist_km, time_start, time_end):
    vel = dist_km / ((time_end - time_start).seconds/3600.0)
    return vel


def calc(item):
    meas1, meas2 = item
    ts1, lat1, lon1 = meas1
    ts2, lat2, lon2 = meas2

    # measure1 must occur first than measure2
    if (ts1 > ts2):
        meas2, meas1 = meas1, meas2
        ts1, lat1, lon1 = meas1
        ts2, lat2, lon2 = meas2
        
    dist = getDistanceFromLatLonInKm(float(lat1), float(lon1), float(lat2), float(lon2))
    v = calc_velocity(
            float(dist), datetime.strptime(ts1, '%Y-%m-%dT%H:%M:%SZ'), datetime.strptime(ts2, '%Y-%m-%dT%H:%M:%SZ'))
    return v


def calculate_velocity(all_values):
    a1 = all_values
    a2 = list(all_values)
    a1.pop()
    a2.pop(0)
    a3 = zip(a1, a2)
    k =  list(map(calc, a3))
    if len(k) == 0:
        return float(0)
    total = 0
    for u in k:
        total += u
    return float(total/len(k))


def takeby2(points):
    """
    Example:
    >>> takeby2([1, 2, 3, 4, 5, 6])
    [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]
    """
    a1 = points
    a2 = list(points)
    a1.pop()
    a2.pop(0)
    return list(zip(a1, a2))


def take_edge(item):
    _, lat1, lon1 = item[0]
    _, lat2, lon2 = item[1]
    return [[float(lat1), float(lon1)], [float(lat2), float(lon2)]]


def value_minus_mean(kmh_list, mean_val):
    for i, u in enumerate(kmh_list):
        kmh_list[i] = abs(u - mean_val)
    return kmh_list


def array_mean(values):
    return sum(values)/len(values)


if __name__ == '__main__':
    spark = SparkSession.builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    udfEdgesUnified = udf(takeby2, ArrayType(ArrayType(ArrayType(StringType()))))
    udfCalculateVelocity = udf(calculate_velocity, DoubleType())
    udfGetEdge = udf(take_edge, ArrayType(ArrayType(DoubleType())))
    udfValueMinusMean = udf(value_minus_mean, ArrayType(DoubleType()))
    udfArrayMean = udf(array_mean, DoubleType())

    df = spark\
            .read\
            .format("json")\
            .load("/tmp/sp_olho_vivo.json", inferSchema=False)\
            .withColumn("ts", col("timestamp").cast(TimestampType()))\
            .orderBy("timestamp")\
            .withColumn("day", dayofyear("ts"))\
            .withColumn("hour", hour("ts"))\
            .withColumn("minute", minute("ts"))\
            .withColumn("edgeWithTimestamp", array(col("timestamp"), col("lat"), col("lon")))\
            .select("ts", "day", "identifier_code", "edgeWithTimestamp")\
            .groupBy("day", "identifier_code")\
            .agg(collect_list(col("edgeWithTimestamp")).alias("edgeWithTimestamp"))\
            .withColumn("edges_unified", udfEdgesUnified(col("edgeWithTimestamp")))\
            .select("day", explode(col("edges_unified")).alias("edge_with_tempo"))\
            .withColumn("edge", udfGetEdge(col("edge_with_tempo")))\
            .withColumn("kmh", udfCalculateVelocity(col("edge_with_tempo")))\
            .groupBy("day").agg(mean("kmh").alias("kmhmean"), collect_list("kmh").alias("kmh_list"))\
            .withColumn("valueminusmean", udfValueMinusMean(col("kmh_list"), col("kmhmean")))\
            .withColumn("mad", udfArrayMean(col("valueminusmean")))
    df.show()
