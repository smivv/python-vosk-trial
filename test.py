#!/usr/bin/env python3
from typing import Optional, AsyncGenerator, Generator

import os
import sys
import logging
import argparse
import subprocess

from vosk import Model, KaldiRecognizer
from pyaudio import PyAudio, Stream, paInt16


# Enable logging if needed
logger = logging.getLogger('websockets')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


class Tester:

    def __init__(
            self,
            filepath: Optional[str],
            model_path: str,
            sample_rate: int,
            use_gpu: bool = False
    ):
        if use_gpu:
            # Gpu part, uncomment if vosk-api has gpu support
            from vosk import GpuInit, GpuInstantiate
            GpuInit()
            GpuInstantiate()

        self.sample_rate = sample_rate
        self.model = Model(model_path)
        self.rec = KaldiRecognizer(self.model, sample_rate)

        self.filepath = filepath

    def _read(self, out):

        while True:
            data = out.read(8000)

            if len(data) == 0:
                break

            if self.rec.AcceptWaveform(data):
                print(self.rec.Result())
            else:
                print(self.rec.PartialResult())

        print(self.rec.FinalResult())

    def _test_microphone(self):

        stream = PyAudio().open(
            format=paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=8000
        )

        stream.start_stream()

        self._read(stream)

    def _test_file(self, filepath):
        process = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i',
                                    filepath, '-ar', str(self.sample_rate),
                                    '-ac', '1', '-f', 's16le', '-'],
                                   stdout=subprocess.PIPE)

        self._read(process.stdout)

    def test(self):
        if self.filepath is None:
            self._test_microphone()
        else:
            self._test_file(self.filepath)


if __name__ == "__main__":

    """
    python3 test.py --sample-rate=8000 --model=...
    python3 test.py --sample-rate=16000 --model=...
    python3 test.py --sample-rate=8000 --model=... --filepath=...
    python3 test.py --sample-rate=16000 --model=... --filepath=...
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model", type=str, required=True, help="Path to the model"
    )
    parser.add_argument(
        "--filepath", type=str, required=False, help="Path to file"
    )
    parser.add_argument(
        "--sample-rate", type=int, required=True, help="Sample rate"
    )
    parser.add_argument(
        "--use-gpu", type=bool, required=False, default=False, help="Port"
    )
    args = parser.parse_args()

    Tester(
        model_path=args.model,
        filepath=args.filepath,
        sample_rate=args.sample_rate,
        use_gpu=args.use_gpu
    ).test()
