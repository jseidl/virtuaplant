#!/bin/sh

echo "VirtuaPlant -- Bottle-filling Factory"
echo "- Starting World View"
./oil_world.py -t localhost &
echo "- Starting HMI"
./oil_hmi.py -t localhost &
