# Parameters

The parameters are immutable in all rounds of this experiment. They are
separated in general, InterSCity specific and InterSCSimulator specific:

## General

- Simulation duration: 1h (from 7a.m. to 8a.m.)
- Traffic accident duration: 30min (from 7:10 a.m. to 7:40 a.m.)
- Traffic boards radius search: 700m
- Number of cars: 100.000
- Traffic boards location: around av. Rebouças (check the input files)
- Traffic accident location: av. Rebouças (check the input files)

## InterSCity specific

- Setup
	- Number of instances of each microservice:
		- Data Collector: 1
		- Resource Discovery: 1
		- Actuator Controller: 1
		- Data Processor: 1
		- Resouce Cataloguer: 1
	- Number of instances of support tools:
		- Kong: 1
		- RabbitMQ: 1
		- Postgres: 1
		- MongoDB: 1
		- Redis: 1
		- Spark: 2 (1 master and 1 worker)
		- Kafka: 1
	- Host configuration:
		- Processor: Intel i7-7500u @ 2.70GHz
		- CPUs: 4
		- RAM: 16GB
		- Fedora 27
		- Linux Kernel 4.15.6
		- Docker 17.12.1-ce
		- Docker-compose 1.17.0
	
## InterSCSimuator specific

- Setup
	- InterSCSimulator: 1 instance
	- Host configuration:
		- Processor: Intel i5-4300U @ 1.90GHz
		- CPUs: 4
		- RAM: 8GB
		- Debian sid
		- Linux kernel 4.16.0
		- Erlang/OTP 20
- Configuration
	- City map: São Paulo city (check input files)
	- Trips: based on Origin-Destination survey (check input files)
