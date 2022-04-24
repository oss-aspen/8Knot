# please run this while in the same folder as the dockerfile 
sudo docker run --rm -it -v $PWD:/explorer --name explorer -p 8050:8050 explorer
