## Installation of prerequisites

### Windows

Remove Windows and install Linux ;)

### Ubuntu

```bash
sudo apt-get install libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0
sudo apt-get install ffmpeg libav-tools

pip install websockets pyaudio vosk
```
### Mac os

```bash
brew install portaudio ffmpeg

pip install websockets pyaudio vosk
```

## Download models

To download models manually go here https://alphacephei.com/vosk/models.  

To download through terminal run these commands:

```bash
# create models directory
mkdir models && cd models

# download archive with light model
curl -L \
https://alphacephei.com/vosk/models/vosk-model-en-us-daanzu-20200905-lgraph.zip > \
vosk-model-en-us-daanzu-20200905-lgraph.zip

# unarchive and delete redundant
unzip vosk-model-en-us-daanzu-20200905-lgraph.zip
rm vosk-model-en-us-daanzu-20200905-lgraph.zip
```

## Vosk Speech recognition trial

### Local test

```bash
# to test with microphone
python test.py --sample-rate=SAMPLE_RATE --model=MODEL_PATH

# to test with file
python test.py --sample-rate=SAMPLE_RATE --model=MODEL_PATH --filepath=FILE_PATH
```

#### Example

```bash
# to test with microphone
python test.py --sample-rate=16000 \
--model=models/vosk-model-en-us-daanzu-20200905-lgraph

# to test with file
python test.py --sample-rate=16000 \
--model=models/vosk-model-en-us-daanzu-20200905-lgraph \
--filepath=wavs/test16k.wav
```

### Websockets service/client

```bash
# to start service
python service.py --sample-rate=SAMPLE_RATE --ip=IP --port=PORT --model=MODEL_PATH

# to test with microphone
python client.py --sample-rate=SAMPLE_RATE --ip=IP --port=PORT

# to test with file
python client.py --sample-rate=SAMPLE_RATE --ip=IP --port=PORT --filepath=FILE_PATH
```

#### Example

```bash
# to start service
python service.py --sample-rate=16000 \
--ip=0.0.0.0 --port=2700 \
--model=models/vosk-model-en-us-daanzu-20200905-lgraph

# to test with microphone
python client.py --sample-rate=16000 --ip=0.0.0.0 --port=2700

# to test with file
python client.py --sample-rate=16000 --ip=0.0.0.0 --port=2700 \
--filepath=wavs/test16k.wav
```

## About

This is a server for highly accurate offline speech recognition using
Kaldi and [Vosk-API](https://github.com/alphacep/vosk-api).

There are four different servers which support four major communication
protocols - MQTT, GRPC, WebRTC and Websocket

The server can be used locally to provide the speech recognition to smart
home, PBX like freeswitch or asterisk. The server can also run as a
backend for streaming speech recognition on the web, it can power
chatbots, websites and telephony.

## Documentation

For documentation and instructions see [Vosk Website](https://alphacephei.com/vosk/server)