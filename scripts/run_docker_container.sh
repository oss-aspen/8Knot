# please run this while in the same folder as the dockerfile 
sudo docker run --rm -it --name explorer -v $PWD:/explorer -p 8050:8050 explorer
