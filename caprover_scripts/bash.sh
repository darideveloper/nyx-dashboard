# Run it inside vps to get bash access to the container
docker exec -it $(docker ps -q --filter "name=srv-captain--nyx-dashboard") bash