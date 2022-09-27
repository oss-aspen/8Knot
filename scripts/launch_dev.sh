# It's common to have access permission denied by the Docker Daemon
# on Linux machines if you don't run Docker with root permissions.

# If containers aren't created because of a 'permission denied' error
# or other by Docker, run this script as '$ sudo bash scripts/launch_dev.sh'

# Docker is working on running rootless but this hasn't been implemented
# yet. It sometimes works on Mac but not always.

# can pass target port number to script for redis as: bash ./this_script.sh <new_port>
# Script builds, connects, and runs the three components of this app: Server, Worker Pool, and Redis instance.

# can pass override target port number to script for redis as: bash ./this_script.sh <new_port>

# if you want more/fewer worker processes in the workerpool, please edit the 'numprocs' field in supervisord.conf

# TODO redis doesn't currently like this and I'm not sure why
if [ -z "$1" ]
    then
        echo "No Redis remap-port supplied."
        echo "Defaulting to port: 6379"
        printf "\n"
        REDIS_PORT_MAP=6379;
    else
        echo "Redis remap-port supplied.";
        echo "Mapping container port 6379 to: $1";
        printf "\n";
        REDIS_PORT_MAP=$1;
fi

# create network for containers 
docker network create eightknot-network ;

# create a redis instance inside of a container, on our docker network, mapped to its respective port. 
docker run --rm -itd --name redis --net eightknot-network -p $REDIS_PORT_MAP:6379 redis;

# grab the route to the redis server from the running redis container
REDIS_CONTAINER_URL=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' redis);
printf "\nRedis URL is: ${REDIS_CONTAINER_URL}:${REDIS_PORT_MAP}\n";

# build and run the worker pool
docker build -f Dockerfile.supervisor_workers -t worker_pool .;
docker run --rm -dit --name worker_pool \
                     --net eightknot-network \
                     --env REDIS_SERVICE_HOST=$REDIS_CONTAINER_URL \
                     --env REDIS_SERVICE_PORT=$REDIS_PORT_MAP \
                     worker_pool;

# build and run the web server
docker build -f Dockerfile.server -t eightknot_server .;
docker run --rm -it --name eightknot_server \
                         --net eightknot-network \
                         --env REDIS_SERVICE_HOST=$REDIS_CONTAINER_URL \
                         --env REDIS_SERVICE_PORT=$REDIS_PORT_MAP \
                         --env-file ./env.list \
                         -p 8050:8050 \
                         eightknot_server;

# cleanup
printf "\nShutting down worker pool...\n"
docker stop worker_pool;

printf "\nShutting down redis...\n"
docker stop redis;

printf "\nRemaining containers:\n"
docker ps -a;

printf "\nDeleting network...\n"
docker network rm eightknot-network;

printf "\nCleanup Done :) \n"
