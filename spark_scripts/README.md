# InterSCity Traffic Anomaly Experiment

## Running Spark Scripts

The `anomaly_detection` scripts gather data from platform data-collector,
trains a M.A.D model and then expect for further outliers. To run the scripts
you should have a functional Spark 2.3.0 build and the python packages listed
in `requirements` file. Then, with Spark binaries in your $PATH, just use
`spark-submit`:
```
$ spark-submit anomaly_detection.py
```

## Running Tests

Inside the `tests` folder, run
```
python3.6 -m pytest  anomaly_detection_test.py
```

## Contact

We are always in #interscity @freenode (IRC). Also, feel free to mail us at
`interscity-platform@googlegroups.com`
