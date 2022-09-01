from __future__ import annotations

from enum import Enum

from soundfile import SoundFile

from nwave import interlocked
from nwave.task import Task, TaskException


class Format(Enum):
    """Audio Formats."""

    AIFF = ("AIFF", "(Apple/SGI)")
    AU = ("AU", "(Sun/NeXT)")
    AVR = ("AVR", "(Audio Visual Research)")
    CAF = ("CAF", "(Apple Core Audio File)")
    FLAC = ("FLAC", "(Free Lossless Audio Codec)")
    HTK = ("HTK", "(HMM Tool Kit)")
    SVX = ("SVX", "(Amiga IFF/SVX8/SV16)")
    MAT4 = ("MAT4", "(GNU Octave 2.0 / Matlab 4.2)")
    MAT5 = ("MAT5", "(GNU Octave 2.1 / Matlab 5.0)")
    MPC2K = ("MPC2K", "(Akai MPC 2k)")
    MP3 = ("MP3", "Audio")
    OGG = ("OGG", "(OGG Container format)")
    PAF = ("PAF", "(Ensoniq PARIS)")
    PVF = ("PVF", "(Portable Voice Format)")
    RAW = ("RAW", "(header-less)")
    RF64 = ("RF64", "(RIFF 64)")
    SD2 = ("SD2", "(Sound Designer II)")
    SDS = ("SDS", "(Midi Sample Dump Standard)")
    IRCAM = ("IRCAM", "(Berkeley/IRCAM/CARL)")
    VOC = ("VOC", "(Creative Labs)")
    W64 = ("W64", "(SoundFoundry WAVE 64)")
    WAV = ("WAV", "(Microsoft)")
    NIST = ("NIST", "(NIST Sphere)")
    WAVEX = ("WAVEX", "(Microsoft)")
    WVE = ("WVE", "(Psion Series 3)")
    XI = ("XI", "(FastTracker 2)")

    def __str__(self) -> str:
        return self.value[0]


class Codec(Enum):
    """Audio Codecs, as sub-specifications of Formats."""

    PCM_S8 = ("PCM_S8", "Signed 8 bit PCM")
    PCM_16 = ("PCM_16", "Signed 16 bit PCM")
    PCM_24 = ("PCM_24", "Signed 24 bit PCM")
    PCM_32 = ("PCM_32", "Signed 32 bit PCM")
    PCM_U8 = ("PCM_U8", "Unsigned 8 bit PCM")
    FLOAT = ("FLOAT", "32 bit float")
    DOUBLE = ("DOUBLE", "64 bit float")
    ULAW = ("ULAW", "U-Law")
    ALAW = ("ALAW", "A-Law")
    IMA_ADPCM = ("IMA_ADPCM", "IMA ADPCM")
    MS_ADPCM = ("MS_ADPCM", "Microsoft ADPCM")
    GSM610 = ("GSM610", "GSM 6.10")
    G721_32 = ("G721_32", "32kbs G721 ADPCM")
    G723_24 = ("G723_24", "24kbs G723 ADPCM")
    G723_40 = ("G723_40", "40kbs G723 ADPCM")
    DWVW_12 = ("DWVW_12", "12 bit DWVW")
    DWVW_16 = ("DWVW_16", "16 bit DWVW")
    DWVW_24 = ("DWVW_24", "24 bit DWVW")
    VOX_ADPCM = ("VOX_ADPCM", "VOX ADPCM")
    NMS_ADPCM_16 = ("NMS_ADPCM_16", "16kbs NMS ADPCM")
    NMS_ADPCM_24 = ("NMS_ADPCM_24", "24kbs NMS ADPCM")
    NMS_ADPCM_32 = ("NMS_ADPCM_32", "32kbs NMS ADPCM")
    DPCM_16 = ("DPCM_16", "16 bit DPCM")
    DPCM_8 = ("DPCM_8", "8 bit DPCM")
    VORBIS = ("VORBIS", "Vorbis")
    OPUS = ("OPUS", "Opus")
    MPEG_LAYER_I = ("MPEG_LAYER_I", "MPEG Layer I")
    MPEG_LAYER_II = ("MPEG_LAYER_II", "MPEG Layer II")
    MPEG_LAYER_III = ("MPEG_LAYER_III", "MPEG Layer III")
    ALAC_16 = ("ALAC_16", "16 bit ALAC")
    ALAC_20 = ("ALAC_20", "20 bit ALAC")
    ALAC_24 = ("ALAC_24", "24 bit ALAC")
    ALAC_32 = ("ALAC_32", "32 bit ALAC")

    def __str__(self) -> str:
        return self.value[0]


def process(task: Task):
    """
    Processes a single file
    """
    # Load
    try:
        with SoundFile(task.file_source) as sf:
            data = sf.read()
            sample_rate = sf.samplerate
            src_format = sf.format
            src_subtype = sf.subtype
    except Exception as ex:
        raise TaskException(ex, "File Loading") from ex

    # Apply Effects
    for effect in task.effects:
        data, sample_rate = effect.apply_trace(data, sample_rate)

    # Write
    try:
        with interlocked.Writer(task.file_output, overwrite=task.overwrite) as file:
            # wavfile.write(file, sample_rate, data)
            with SoundFile(
                file,
                mode="w",
                samplerate=round(sample_rate),
                channels=data.shape[1] if len(data.shape) > 1 else 1,
                format=task.format if task.format else src_format,
                subtype=task.codec if task.codec else src_subtype,
            ) as sf:
                sf.write(data)
    except Exception as ex:
        raise TaskException(ex, "File Writing") from ex
