import pytest
import findspark
findspark.init()
import pyspark
import tests
from anomaly_detection import *

@pytest.fixture
def spark():
    return pyspark.sql.SparkSession.builder.getOrCreate()


@pytest.fixture
def sc():
    return pyspark.SparkContext.getOrCreate()


def testTakeBy2():
    points = [1,2,3,4,5,6]
    assert takeBy2(points)==[(1,2),(2,3),(3,4),(4,5),(5,6)]
    points = []
    assert takeBy2(points)==[]
    points = [1]
    assert takeBy2(points)==[(1,1)]


def testTakeEdge():
    item = [["something", 100, 150], ["something2", 200, 250]]
    assert takeEdge(item)==[[100, 150], [200, 250]]


def testValueMinusMean():
    meanval = 3
    values = [1,2,3,4,5]
    assert valueMinusMean(values, meanval)==[
        abs(1-3),abs(2-3),abs(3-3),abs(4-3),abs(5-3)
    ]


def testMedian():
    values = [1,2,3,4,5]
    assert median(values)==3
    values = [1, 2, 3, 3, 4, 4, 4, 5, 5.5, 6, 6, 6.5, 7, 7, 7.5, 8, 9, 12, 52, 90]
    assert median(values)==6


def testJsonExtraction(spark, sc):
    jsonString = """{"uuid": "aaaa", "capability": "temperature"}"""
    df = spark.createDataFrame([(jsonString,),], ["value"])
    df.show(truncate=False)
    val = df.select(extractJsonFromString(df, ["uuid", "capability"])).rdd.collect()[0]
    assert val["uuid"]=="aaaa"
    assert val["capability"]=="temperature"


def testMad(spark):
    values = [ (1.,"a",), (2.,"a",), (3.,"a",), (3.,"a",), (4.,"a",), (4.,"a",),
            (5.,"a",), (5.5,"a",), (6.,"a",), (6.,"a",), (6.5,"a",), (7.,"a",),
            (7.,"a",), (7.5,"a",), (8.,"a",), (9.,"a",), (12.,"a",), (52.,"a",),
            (90.,"a",),]
    df = spark.createDataFrame(values, ["data", "id"])
    mad = calculatesMad(df.groupBy("id"), "data").rdd.collect()[0]["mad"]
    assert mad==2
