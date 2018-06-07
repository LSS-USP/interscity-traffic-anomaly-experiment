#!/bin/bash

DOCKER_IMAGE="kanashiro/interscsimulator:stable-0.1"
RABBITMQ_HOST=10.142.0.4
INPUT_DIR="./interscsimulator_input_baseline"
OUTPUT_DIR="./interscsimulator_output"
ROUNDS=1

echo "[I] Creating docker-compose file"
cat > docker-compose.yml << EOF
version: '3'
services:
    simulator:
        image: $DOCKER_IMAGE
        environment:
            - RABBITMQ_HOST=$RABBITMQ_HOST
        network_mode: "host"
        tty: true
        volumes:
            - $OUTPUT_DIR:/interscsimulator/mock-simulators/smart_city_model/output
            - $INPUT_DIR:/interscsimulator/mock-simulators/smart_city_model/input
EOF

for i in $(seq 1 $ROUNDS)
do
	echo "[I] docker-compose.yml content"
	cat docker-compose.yml

	echo "[I] Running docker-compose"
	mkdir -p logs
	sudo docker-compose up > logs/round_"$i".log

	echo "[I] Moving events.xml file to output dir"
	mkdir -p output
	mv $OUTPUT_DIR/events.xml ouput/events_round_"$1".xml

	echo "[I] Running docker-compose down"
	sudo docker-compose down
done
