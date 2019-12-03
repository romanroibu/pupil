"""
(*)~---------------------------------------------------------------------------
Pupil - eye tracking platform
Copyright (C) 2012-2019 Pupil Labs

Distributed under the terms of the GNU
Lesser General Public License (LGPL v3.0).
See COPYING and COPYING.LESSER for license details.
---------------------------------------------------------------------------~(*)
"""
import time
import logging
import threading
import typing as T
from pathlib import Path

from pupil_audio.nonblocking import PyAudio2PyAVCapture

from stdlib_utils import create_temporary_unique_file_path
from observable import Observable


logger = logging.getLogger(__name__)


class AudioMicCheckController(Observable):
    def __init__(self):
        # Public
        self.source_name = None
        self.mic_check_duration_sec = 3
        # Private
        self._status_string = self._status_str_idle()
        self._checking_thread = None

    # Public

    @property
    def is_checking(self) -> bool:
        return self._checking_thread is not None

    @property
    def can_perform_check(self) -> bool:
        return self.source_name is not None

    @property
    def status_string(self) -> str:
        return self._status_string

    def perform_check(self):
        if self.source_name is None:
            logger.debug("No audio source selected. Skipping audio capture.")
            return
        if self.is_checking:
            logger.debug("AudioMicCheckController.perform_check called on an already busy instance")
            return
        self._status_string = self._status_str_checking()
        self._checking_thread = threading.Thread(
            name=type(self).__class__.__name__,
            target=self._mic_check_fn,
            args=(self.source_name, self.mic_check_duration_sec),
            daemon=True,
        )
        self._checking_thread.start()

    def _close(self):
        if self._checking_thread is not None:
            self._checking_thread.join()
            self._checking_thread = None

    def cleanup(self):
        pass

    # Callbacks

    def on_check_started(self):
        pass

    def on_check_finished(self):
        pass

    # Private

    def _status_str_idle(self) -> str:
        return ""

    def _status_str_checking(self) -> str:
        return "Checking mic..."

    def _status_str_success(self) -> str:
        return "Mic check successfull"

    def _status_str_failure(self, reason) -> str:
        return f"Mic check failed: {reason}"

    def _mic_check_fn(self, in_name, duration):
        out_path = create_temporary_unique_file_path(ext=".mp4")
        start_time = time.monotonic()
        sleep_step = 0.1
        capture = None

        self.on_check_started()

        try:
            capture = PyAudio2PyAVCapture(
                in_name=in_name,
                out_path=str(out_path),
            )
            capture.start()
            while time.monotonic() - start_time < duration:
                time.sleep(sleep_step)

            self._validate_out_file(out_path)

            out_path.unlink()

            self._status_string = self._status_str_success()

        except Exception as err:
            self._status_string = self._status_str_failure(err)

        finally:
            if capture is not None:
                capture.stop()
            self._checking_thread = None
            self.on_check_finished()


    @staticmethod
    def _validate_out_file(out_path: Path) -> T.Tuple[bool, str]:
        if not out_path.is_file():
            raise ValueError("Recorded file was not saved")

        if out_path.stat().st_size == 0:
            raise ValueError("Recorded file is empty")

        return True
