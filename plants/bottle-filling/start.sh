#!/bin/sh

echo "VirtuaPlant -- Bottle-filling Factory"
echo "- Starting World View"
./world.py &
echo "- Starting HMI"
./hmi.py &
