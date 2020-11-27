#!/usr/bin/env python3
from typing import Optional, AsyncGenerator, Generator

import json
import os
import sys
import asyncio
import pathlib
import logging
import argparse
import websockets

from pyaudio import PyAudio, Stream, paInt16
from contextlib import asynccontextmanager, contextmanager, AsyncExitStack


# Enable logging if needed
logger = logging.getLogger("websockets")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


class Client:

    def __init__(
            self,
            filepath: Optional[str],
            sample_rate: int,
            ip: str,
            port: int,
    ):
        self.filepath = filepath
        self.sample_rate = sample_rate

        self.ip = ip
        self.port = port

    @contextmanager
    def _pyaudio(self) -> Generator[PyAudio, None, None]:
        p = PyAudio()
        try:
            yield p
        finally:
            print("Terminating PyAudio object")
            p.terminate()

    @contextmanager
    def _pyaudio_open_stream(
            self,
            p: PyAudio, *args, **kwargs
    ) -> Generator[Stream, None, None]:

        s = p.open(*args, **kwargs)
        try:
            yield s
        finally:
            print("Closing PyAudio Stream")
            s.close()

    @asynccontextmanager
    async def _polite_websocket(
            self,
            ws: websockets.WebSocketClientProtocol
    ) -> AsyncGenerator[websockets.WebSocketClientProtocol, None]:
        try:
            yield ws
        finally:
            print("Terminating connection")
            await ws.send("{\"eof\" : 1}")
            print(await ws.recv())

    @property
    def uri(self):
        return f"ws://{self.ip}:{self.port}"

    async def _test_microphone(self):
        async with AsyncExitStack() as stack:
            ws = await stack.enter_async_context(
                websockets.connect(self.uri)
            )
            print(f"Connected to {self.uri}")
            print("Type Ctrl-C to exit")
            ws = await stack.enter_async_context(self._polite_websocket(ws))
            p = stack.enter_context(self._pyaudio())
            s = stack.enter_context(
                self._pyaudio_open_stream(
                    p,
                    format=paInt16,
                    channels=1,
                    rate=self.sample_rate,
                    input=True,
                    frames_per_buffer=8000
                )
            )

            while True:
                data = s.read(self.sample_rate)
                if len(data) == 0:
                    break
                await ws.send(data)
                print(await ws.recv())

    async def _test_file(self):
        async with websockets.connect(self.uri) as websocket:
            proc = await asyncio.create_subprocess_exec(
                'ffmpeg', '-nostdin', '-loglevel', 'quiet', '-i', self.filepath,
                '-ar', str(self.sample_rate), '-ac', '1', '-f', 's16le', '-',
                stdout=asyncio.subprocess.PIPE
            )

            while True:
                data = await proc.stdout.read(8000)

                if len(data) == 0:
                    break

                await websocket.send(data)
                print(await websocket.recv())

            await websocket.send('{"eof" : 1}')
            print(await websocket.recv())

    def test(self):
        if self.filepath is None:
            try:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self._test_microphone())
            except (Exception, KeyboardInterrupt) as e:
                loop.stop()
                loop.run_until_complete(loop.shutdown_asyncgens())
                if isinstance(e, KeyboardInterrupt):
                    print("Bye")
                    exit(0)
                else:
                    print(f"Oops! {e}")
                    exit(1)
        else:
            asyncio.get_event_loop().run_until_complete(self._test_file())


if __name__ == "__main__":
    """
    python3 test.py --sample-rate=8000 --ip=0.0.0.0 --port=2700
    python3 test.py --sample-rate=8000 --ip=0.0.0.0 --port=2700 --filepath=...
    python3 test.py --sample-rate=16000 --ip=0.0.0.0 --port=2700
    python3 test.py --sample-rate=16000 --ip=0.0.0.0 --port=2700 --filepath=...
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--filepath", type=str, required=False, help="Path to the audiofile"
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
    args = parser.parse_args()

    Client(
        filepath=args.filepath,
        sample_rate=args.sample_rate,
        ip=args.ip,
        port=args.port,
    ).test()
