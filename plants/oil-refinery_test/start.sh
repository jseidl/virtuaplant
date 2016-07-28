#!/bin/sh

echo "VirtuaPlant -- Bottle-filling Factory"
echo "- Starting World View"
./oil_world.py &
echo "- Starting HMI"
./oil_hmi.py &
