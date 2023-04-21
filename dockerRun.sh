docker stop python_tts
docker rm python_tts

docker build -t python_tts .
docker run --name python_tts -p 2020:2020 \
-d python_tts


