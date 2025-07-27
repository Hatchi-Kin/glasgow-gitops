#!/bin/bash
# A simple script to generate load on the FastAPI health endpoint.

URL="http://fastapi.192.168.1.20.nip.io/health"
CONCURRENT_REQUESTS=15

echo "Starting load test on $URL with $CONCURRENT_REQUESTS concurrent requests."
echo "Press [CTRL+C] to stop."

# Start background loops
for i in $(seq 1 $CONCURRENT_REQUESTS)
do
  # Each loop continuously curls the URL
  while true
  do
    curl -s -o /dev/null "$URL"
  done &
done

# Wait for all background jobs to finish (which they won't, until CTRL+C)
wait
