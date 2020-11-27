#!/usr/bin/env python3

import json
import os
import sys
import asyncio
import pathlib
import logging
import argparse
import websockets

from concurrent.futures import ThreadPoolExecutor
from vosk import Model, KaldiRecognizer


# Enable logging if needed
logger = logging.getLogger('websockets')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


class Server:

    def __init__(
            self,
            model_path: str,
            sample_rate: int,
            ip: str,
            port: int,
            gpu: bool = False
    ):
        self.model = Model(model_path)
        self.sample_rate = sample_rate

        self.ip = ip
        self.port = port

        self.pool = None
        self.loop = None

        self.gpu = gpu

    def serve(self):

        if self.gpu:
            # Gpu part, uncomment if vosk-api has gpu support
            from vosk import GpuInit, GpuInstantiate
            GpuInit()

            def thread_init():
                GpuInstantiate()

            self.pool = ThreadPoolExecutor(initializer=thread_init)
        else:
            self.pool = ThreadPoolExecutor((os.cpu_count() or 1))

        self.loop = asyncio.get_event_loop()

        start_server = websockets.initialize(
            self._recognize,
            self.ip,
            self.port
        )

        self.loop.run_until_complete(start_server)
        self.loop.run_forever()

    def _process_chunk(self, rec, message):
        if message == '{"eof" : 1}':
            return rec.FinalResult(), True
        elif rec.AcceptWaveform(message):
            return rec.Result(), False
        else:
            return rec.PartialResult(), False

    async def _recognize(self, websocket, path):
        rec = None
        phrase_list = None

        while True:

            message = await websocket.recv()

            # Load configuration if provided
            if isinstance(message, str) and 'config' in message:
                jobj = json.loads(message)['config']
                if 'phrase_list' in jobj:
                    phrase_list = jobj['phrase_list']
                if 'sample_rate' in jobj:
                    sample_rate = float(jobj['sample_rate'])
                continue

            # Create the recognizer, word list is temporary disabled
            # since not every model supports it
            if not rec:
                if phrase_list:
                    rec = KaldiRecognizer(self.model, self.sample_rate,
                                          json.dumps(phrase_list))
                else:
                    rec = KaldiRecognizer(self.model, self.sample_rate)

            response, stop = \
                await self.loop.run_in_executor(
                    self.pool, self._process_chunk, rec, message)
            await websocket.send(response)
            if stop:
                break


if __name__ == "__main__":

    """
    python3 serve.py --sample-rate=8000 --ip=0.0.0.0 --port=2700 --model=...
    python3 serve.py --sample-rate=16000 --ip=0.0.0.0 --port=2700 --model=...
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", type=str, required=True, help="Path to the model"
    )
    parser.add_argument(
        "--sample-rate", type=int, required=True, help="Sample rate"
    )
    parser.add_argument(
        "--ip", type=str, required=True, help="IP"
    )
    parser.add_argument(
        "--port", type=int, required=True, help="Port"
    )
    parser.add_argument(
        "--gpu", type=bool, required=False, default=False, help="Port"
    )
    args = parser.parse_args()

    Server(
        model_path=args.model,
        sample_rate=args.sample_rate,
        ip=args.ip,
        port=args.port,
        gpu=args.use_gpu
    ).serve()
