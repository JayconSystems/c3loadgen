#!/bin/bash

name=c3loadgen

sh -c "while /bin/true; do inotifywait -e modify -r .; docker stop $name; done" &

while /bin/true; do
    docker kill $name
    docker rm $name
    docker build -t $name .
    docker run -it --name $name \
	   --link demo-db:mysql --link c3ld:c3ld $name
    sleep 2
done
