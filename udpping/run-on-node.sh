#!/bin/bash -e

MONROE_NAMESPACE=$(docker ps --no-trunc -aqf name=monroe-namespace)

DIR=/run/shm/test0
rm -rf $DIR
mkdir -p $DIR
echo '{"nodeid": "999", "measurement_id": "99999", "interface": "op0", "network_id": "99"}' >$DIR/config
mkdir -p $DIR/results

docker run -d --name test0 --net=container:$MONROE_NAMESPACE   -v $DIR/results:/monroe/results -v $DIR/config:/monroe/config:ro dreibh/udpping
