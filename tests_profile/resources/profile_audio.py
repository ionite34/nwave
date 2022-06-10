import logging

import ffmpeg

from nwave import Task


def process_ffmpeg(task: Task) -> (int, Task):
    stream = ffmpeg.input(task.file_source)
    # Add silence padding to beginning
    pad_s = task.config.silence_padding[0]
    stream = ffmpeg.filter(stream, "adelay", pad_s)
    # Add silence padding to end
    pad_e = task.config.silence_padding[1]
    stream = ffmpeg.filter(stream, "apad", f"pad_dur={pad_e}")
    # Output as resampled
    stream = ffmpeg.output(stream, task.file_output, ac=1, ar=task.config.sample_rate)
    out, err = None, None
    try:
        out, err = ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, overwrite_output=True)
    except ffmpeg.Error as e:
        logging.error(f"Error running ffmpeg: {err}")
        return 1, task
    return 0, task
