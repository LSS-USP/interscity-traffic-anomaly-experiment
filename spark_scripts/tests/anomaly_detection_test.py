import pytest
import findspark
findspark.init()
import pyspark
import tests
from anomaly_detection import *


def testGetDistance():
    assert getDistance(-3, 2, 3, 5)==3*sqrt(5)


def testVelocityFormula():
    item = [[100, -3, 2], [200, 3, 5]]
    assert velocityFormula(item)==((3*sqrt(5))/100.0)
    # order-secure
    item = [[200, 3, 5], [100, -3, 2]]
    assert velocityFormula(item)==((3*sqrt(5))/100.0)


def testTakeBy2():
    points = [1,2,3,4,5,6]
    assert takeBy2(points)==[(1,2),(2,3),(3,4),(4,5),(5,6)]


def testTakeEdge():
    item = [["something", 100, 150], ["something2", 200, 250]]
    assert takeEdge(item)==[[100, 150], [200, 250]]


def testValueMinusMean():
    meanval = 3
    values = [1,2,3,4,5]
    assert valueMinusMean(values, meanval)==[
        abs(1-3),abs(2-3),abs(3-3),abs(4-3),abs(5-3)
    ]


def testArrayMean():
    values = [1,2,3,4,5]
    assert array_mean(values)==3
