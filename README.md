# UDP Ping for OpenWRT

Files in this branch are used to compile and deploy containers running UDP ping measuremenets on Celerway OS (OpenWRT) nodes.  This OS is quite different from Debian 7 we used to use.  It includes some simplifications, for instance, metadata is available via internal (on-node) API:

## Build and deploy

$ docker compose build
$ docker push crnaeng/udppingh

On the node:

$ docker compose up

The results of the measurements are written to /home/nne/nne/results

## Interfacing with the router
 
As of summer 2023, the Celerway OS core utilities offer the same REST API that we have on the MONROE nodes, i.e. 
the equivalent of the dlbinfo command:

$ curl localhost:88/dlb|jq .

the equivalent of the modems command:

$ curl localhost:88/modems/update|jq .

From LAN clients, basic authentication is required, so from inside our container (in alpine, you need to apk add curl jq), we would use:

$ curl -u admin:celerway http://192.168.5.1/dlb | jq .

## Design principles

1) Minimal changes to measurement scripts in folder 'files'
2) Maximal simplification. We use 'alpine' base image, and add packages we have to have

## Notes

The container can be built on Mac.  It is prepared for AMD, and will run on nodes (tested at Pilius 6365)
