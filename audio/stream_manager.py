import sounddevice as sd
from .engine import AudioEngine


class StreamManager:
    def __init__(self, app):
        self.app = app
        self.state = app.state

        self.input_stream = None
        self.vb_stream = None
        self.monitor_stream = None

        self.blocksize = 256
        self.samplerate = 48000

        self.engine = AudioEngine(self.state)

    def audio_callback(self, indata, frames, time, status):

        if status:
            status_text = str(status).lower()
            if "input overflow" not in status_text:
                print(status)

        try:

            processed = self.engine.process(indata) * self.state.volume

            if self.vb_stream and self.vb_stream.active:

                out = processed

                if self.vb_stream.channels == 2:
                    out = out.repeat(2, axis=1)

                self.vb_stream.write(out)

            if (
                self.state.monitor_on
                and self.monitor_stream
                and self.monitor_stream.active
            ):

                out = processed * self.state.monitor_volume

                if self.monitor_stream.channels == 2:
                    out = out.repeat(2, axis=1)

                self.monitor_stream.write(out)

        except Exception as e:
            print("Blad callbacku audio:", e)

    def start(self):
        self.restart(
            self.state.default_input_device,
            self.state.default_output_device,
        )

    def restart(self, input_id=None, monitor_output_id=None):

        self.stop()

        devices = sd.query_devices()

        try:
            device_info = sd.query_devices(input_id)
            self.samplerate = int(device_info["default_samplerate"])
        except:
            self.samplerate = 48000

        self.engine = AudioEngine(self.state, self.samplerate)

        try:
            self.input_stream = sd.InputStream(
                device=input_id,
                channels=1,
                samplerate=self.samplerate,
                blocksize=self.blocksize,
                dtype="float32",
                callback=self.audio_callback,
            )

            self.input_stream.start()

        except Exception as e:
            print("Blad strumienia wejscia:", e)
            self.input_stream = None

        vb_device_id = None

        for i, d in enumerate(devices):

            name = d["name"].lower()

            if "wdm-ks" in name:
                continue

            if "cable input" in name and d["max_output_channels"] > 0:
                vb_device_id = i
                break

        if vb_device_id is None:
            for i, d in enumerate(devices):
                name = d["name"].lower()
                if "vb-audio" in name and d["max_output_channels"] > 0:
                    vb_device_id = i
                    break

        self.vb_stream = None

        if vb_device_id is not None:

            try:

                vb_info = devices[vb_device_id]

                vb_channels = vb_info["max_output_channels"]

                if vb_channels < 1:
                    vb_channels = 1

                if vb_channels > 2:
                    vb_channels = 2

                self.vb_stream = sd.OutputStream(
                    device=vb_device_id,
                    channels=vb_channels,
                    samplerate=self.samplerate,
                    blocksize=self.blocksize,
                    dtype="float32",
                    latency="low",
                )

                self.vb_stream.start()

                print("VB Cable OK:", vb_info["name"], "kanaly:", vb_channels)

            except Exception as e:
                print("Blad strumienia VB:", e)
                self.vb_stream = None

        else:
            print("VB Cable nie znaleziony")

        self.monitor_stream = None

        if monitor_output_id is not None:

            try:

                self.monitor_stream = sd.OutputStream(
                    device=monitor_output_id,
                    channels=1,
                    samplerate=self.samplerate,
                    blocksize=self.blocksize,
                    dtype="float32",
                    latency="low",
                )

                if self.state.monitor_on:
                    self.monitor_stream.start()

            except Exception as e:
                print("Blad strumienia monitoru:", e)
                self.monitor_stream = None

    def update_monitor_state(self):
        if not self.monitor_stream:
            return

        try:
            if self.state.monitor_on:
                if not self.monitor_stream.active:
                    self.monitor_stream.start()
            else:
                if self.monitor_stream.active:
                    self.monitor_stream.stop()
        except:
            pass

    def stop(self):
        for s in [self.input_stream, self.vb_stream, self.monitor_stream]:
            if s:
                try:
                    s.stop()
                    s.close()
                except:
                    pass
