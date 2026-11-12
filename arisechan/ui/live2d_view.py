import json
import math
import random
from pathlib import Path

from pyopengltk import OpenGLFrame

from arisechan.services.motion_commands import MOTION_COUNT, MOTION_SEQUENCES


LIVE2D_TRANSPARENT = "#010101"
LIVE2D_TRANSPARENT_RGB = (1 / 255, 1 / 255, 1 / 255)
EYE_TRACKING_PARAMETERS = ("ParamEyeBallX", "ParamEyeBallY")
HEAD_TRACKING_PARAMETERS = ("ParamAngleX", "ParamAngleY")
GAZE_SMOOTHING = 0.4
EYE_POSITION_Y_RATIO = 0.38
HEAD_TRACKING_X_DEGREES = 10
HEAD_TRACKING_Y_DEGREES = 6


def _normalized_gaze(pointer_x, pointer_y, eye_x, eye_y, screen_width, screen_height):
    return (
        max(-1.0, min(1.0, (pointer_x - eye_x) / (screen_width / 2))),
        max(-1.0, min(1.0, (eye_y - pointer_y) / (screen_height / 2))),
    )


class Live2DView(OpenGLFrame):
    FRAME_INTERVAL_MS = 33
    IDLE_FRAME_INTERVAL_MS = 50
    MOTION_GROUP = ""

    def __init__(self, master, model_path, on_error, width, height, on_ready=None):
        super().__init__(
            master,
            width=width,
            height=height,
            borderwidth=0,
            highlightthickness=0,
        )
        self.model_path = Path(model_path)
        self.on_error = on_error
        self.on_ready = on_ready
        self.ready_notified = False
        self.live2d = None
        self.model = None
        self.motion_count = 0
        self.motion_durations = []
        self.motion_timer_id = None
        self.pending_motion_index = None
        self.pending_sequence = None
        self.motion_queue = []
        self.eye_parameter_ranges = {}
        self.gaze_x = 0.0
        self.gaze_y = 0.0
        self.follow_cursor = True
        self.screen_width = 0
        self.screen_height = 0
        self.failed = False
        self.shutdown_requested = False
        self.runtime_initialized = False

    def initgl(self):
        if self.failed or self.shutdown_requested:
            return

        try:
            if not self.screen_width or not self.screen_height:
                self.screen_width = self.winfo_screenwidth()
                self.screen_height = self.winfo_screenheight()

            if self.live2d is None:
                import live2d

                self.live2d = live2d
                live2d.init()
                self.runtime_initialized = True
                live2d.glInit()

            if self.model is None:
                if not self.model_path.is_file():
                    raise FileNotFoundError(
                        f"Live2D model file not found: {self.model_path}"
                    )

                self.model = self.live2d.Model()
                self.model.LoadModelJson(str(self.model_path))
                self.motion_count = self.model.GetMotionCount(self.MOTION_GROUP)
                if self.motion_count == 0:
                    raise RuntimeError("The Live2D model does not contain any motions.")
                self.motion_durations = self._load_motion_durations()
                if len(self.motion_durations) != self.motion_count:
                    raise RuntimeError(
                        "The Live2D motion metadata does not match the model."
                    )
                self.eye_parameter_ranges = {
                    parameter: (
                        self.model.GetParamMinById(parameter),
                        self.model.GetParamMaxById(parameter),
                    )
                    for parameter in (
                        *EYE_TRACKING_PARAMETERS,
                        *HEAD_TRACKING_PARAMETERS,
                    )
                }
                if any(
                    minimum >= maximum
                    for minimum, maximum in self.eye_parameter_ranges.values()
                ):
                    raise RuntimeError(
                        "The Live2D eye-tracking parameters have invalid ranges."
                    )

                self.model.SetAutoBlink(True)
                self.model.SetAutoBreath(True)
                self._start_idle_motion()

            self.model.Resize(self.width, self.height)
            if self.pending_sequence is not None:
                sequence_name = self.pending_sequence
                self.pending_sequence = None
                self.play_sequence(sequence_name)
            elif self.pending_motion_index is not None:
                motion_index = self.pending_motion_index
                self.pending_motion_index = None
                self.play_motion(motion_index)
        except Exception as error:
            self.failed = True
            self.animate = 0
            self.after_idle(lambda error=error: self.on_error(error))

    def _load_motion_durations(self):
        motions = self.model.GetMotions().get(self.MOTION_GROUP, [])
        durations = []
        for motion in motions:
            path = self.model_path.parent / motion["File"]
            data = json.loads(path.read_text(encoding="utf-8"))
            durations.append(float(data["Meta"]["Duration"]))
        return durations

    def redraw(self):
        if self.failed or self.shutdown_requested or self.model is None:
            return

        self.live2d.clearBuffer(*LIVE2D_TRANSPARENT_RGB, 0.0)
        self.model.Update()
        self._update_gaze()
        self.model.Draw()
        if not self.ready_notified:
            self.ready_notified = True
            if self.on_ready:
                self.after_idle(self.on_ready)

    def _update_gaze(self):
        if self.follow_cursor:
            pointer_x = self.winfo_pointerx()
            pointer_y = self.winfo_pointery()
            eye_x = self.winfo_rootx() + self.width / 2
            eye_y = self.winfo_rooty() + self.height * EYE_POSITION_Y_RATIO
            target_x, target_y = _normalized_gaze(
                pointer_x,
                pointer_y,
                eye_x,
                eye_y,
                self.screen_width,
                self.screen_height,
            )
        else:
            target_x = target_y = 0.0
        self.gaze_x += (target_x - self.gaze_x) * GAZE_SMOOTHING
        self.gaze_y += (target_y - self.gaze_y) * GAZE_SMOOTHING

        for parameter, gaze in zip(
            EYE_TRACKING_PARAMETERS,
            (self.gaze_x, self.gaze_y),
        ):
            minimum, maximum = self.eye_parameter_ranges[parameter]
            value = minimum + (gaze + 1) * (maximum - minimum) / 2
            self.model.SetParamById(parameter, value)

        for parameter, gaze, maximum_offset in (
            ("ParamAngleX", self.gaze_x, HEAD_TRACKING_X_DEGREES),
            ("ParamAngleY", self.gaze_y, HEAD_TRACKING_Y_DEGREES),
        ):
            minimum, maximum = self.eye_parameter_ranges[parameter]
            current = self.model.GetParamValueById(parameter)
            value = max(
                minimum,
                min(maximum, current + gaze * maximum_offset),
            )
            self.model.SetParamById(parameter, value)

    def set_follow_cursor(self, enabled):
        self.follow_cursor = bool(enabled)

    def play_reaction(self):
        motion_count = self.motion_count or MOTION_COUNT + 1
        if motion_count <= 1:
            return None

        motion_index = random.randrange(1, motion_count)
        return motion_index if self.play_motion(motion_index) else None

    def play_motion(self, motion_index):
        if self.failed or self.shutdown_requested:
            return False
        if not 1 <= motion_index <= MOTION_COUNT:
            raise ValueError(f"Motion number must be between 1 and {MOTION_COUNT}.")
        if self.motion_count and motion_index >= self.motion_count:
            return False
        if self.model is None:
            self.pending_sequence = None
            self.motion_queue.clear()
            self.pending_motion_index = motion_index
            return True

        self.pending_sequence = None
        self.pending_motion_index = None
        self.motion_queue.clear()
        return self._start_motion(motion_index)

    def play_sequence(self, sequence_name):
        if self.failed or self.shutdown_requested:
            return False
        sequence = MOTION_SEQUENCES.get(sequence_name)
        if sequence is None:
            raise ValueError(f"Unknown animation sequence: {sequence_name}")
        if self.motion_count and any(index >= self.motion_count for index in sequence):
            return False

        self.pending_motion_index = None
        if self.model is None:
            self.motion_queue.clear()
            self.pending_sequence = sequence_name
            return True

        self.pending_sequence = None
        self.motion_queue = list(sequence)
        return self._play_next_motion()

    def _start_motion(self, motion_index):
        self._cancel_motion_timer()
        self.animate = self.FRAME_INTERVAL_MS
        self.model.StopAllMotions()
        self.model.StartMotion(
            self.MOTION_GROUP,
            motion_index,
            self.live2d.MotionPriority.FORCE,
        )
        duration_ms = math.ceil(self.motion_durations[motion_index] * 1000)
        self.motion_timer_id = self.after(
            duration_ms + self.FRAME_INTERVAL_MS,
            self._finish_motion,
        )
        return True

    def return_to_idle(self):
        if self.failed or self.shutdown_requested:
            return False
        self.pending_motion_index = None
        self.pending_sequence = None
        self.motion_queue.clear()
        if self.model is None:
            return True
        self._start_idle_motion()
        return True

    def _finish_motion(self):
        self.motion_timer_id = None
        if self.motion_queue:
            self._play_next_motion()
        else:
            self._start_idle_motion()

    def _play_next_motion(self):
        if not self.motion_queue:
            self._start_idle_motion()
            return False
        return self._start_motion(self.motion_queue.pop(0))

    def _start_idle_motion(self):
        if self.model is None:
            return
        self._cancel_motion_timer()
        self.animate = self.IDLE_FRAME_INTERVAL_MS
        self.model.StopAllMotions()
        self.model.StartMotion(
            self.MOTION_GROUP,
            0,
            self.live2d.MotionPriority.IDLE,
        )

    def _cancel_motion_timer(self):
        if self.motion_timer_id is not None:
            self.after_cancel(self.motion_timer_id)
            self.motion_timer_id = None

    def shutdown(self):
        if self.shutdown_requested:
            return

        self.shutdown_requested = True
        self.animate = 0
        self.motion_queue.clear()
        self.pending_motion_index = None
        self.pending_sequence = None
        self._cancel_motion_timer()
        if self.cb is not None:
            self.after_cancel(self.cb)
            self.cb = None

        if self.live2d is not None and self.runtime_initialized:
            if self.context_created:
                self.tkMakeCurrent()
            self.model = None
            self.live2d.dispose()
            self.live2d = None
            self.runtime_initialized = False
