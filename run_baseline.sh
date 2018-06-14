#!/bin/bash

DOCKER_IMAGE="kanashiro/interscsimulator:1.5"
RABBITMQ_HOST=10.142.0.5
INPUT_DIR="./interscsimulator_input_baseline"
OUTPUT_DIR="./interscsimulator_output"
ROUNDS=1
PLATFORM_ALIAS=platform

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
	echo "================================================================"
	echo "[I] Starting round $i at $(date)"

	echo "[I] docker-compose.yml content"
	cat docker-compose.yml

	echo "[I] Running docker-compose"
	mkdir -p logs
	sudo docker-compose up > logs/round_"$i".log

#   echo "[I] Removing data-collector from remote host"
#   gcloud compute ssh dguedes@$PLATFORM_ALIAS --command=<<- Command
# cd dev-env/data-collector
# sudo docker-compose down
# sudo docker-compose up -d
# Command

	echo "[I] Running docker-compose down"
	sudo docker-compose down

	echo "[I] Moving events.xml file to output dir"
	mkdir -p output
	cp $OUTPUT_DIR/events.xml output/events_round_"$i".xml

	echo "[I] Finishing round $i at $(date)"
	echo "================================================================"
done
