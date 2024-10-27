#!/bin/bash
source ./environment_mac.txt
podman machine init
podman machine start

pip3 install podman-compose --break-system-packages
podman-compose down
podman-compose up -d --build
podman logs -f finaillm-ingestion