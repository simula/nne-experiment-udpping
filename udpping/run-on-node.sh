#!/bin/bash -e

MONROE_NAMESPACE=$(docker ps --no-trunc -aqf name=monroe-namespace)

WORKDIR=/run/shm/test0
rm -rf $WORKDIR
mkdir -p $WORKDIR
echo '{ "node_id": "999", "instances": [ { "measurement_id": "99999", "interface": "op0", "network_id": "99" }, { "measurement_id": "99998", "interface": "op1", "network_id": "98" } ] }
' >$WORKDIR/config
mkdir -p $WORKDIR/results

docker run -d --name test0 --net=container:$MONROE_NAMESPACE   -v $WORKDIR/results:/monroe/results -v $WORKDIR/config:/monroe/config:ro dreibh/udpping
