import wave
import numpy as np
import struct
import sys
import scipy.io.wavfile as wavfile

def write_wav_file(filename, sample_rate, n_channels, data):
    data = np.array(data, dtype=np.int16)
    data = struct.pack('<{}h'.format(len(data)), *data)
    wav_file = wave.open(filename, 'wb')
    wav_file.setnchannels(n_channels)
    wav_file.setsampwidth(2)
    wav_file.setframerate(sample_rate)
    wav_file.writeframes(data)
    wav_file.close()

def load_wav_data(filename):
  (rate, samples) = wavfile.read(filename)

  if len(samples.shape) == 1:
    # Ensure that single-channel wavs are the same shape as n-channel
    samples = np.reshape(samples, (1, len(samples)))
  else:
    samples = samples.T

  # Scale all values to -1..1
  samples = np.divide(samples.astype(np.float64), np.iinfo(samples[0][0]).max)

  return (rate, samples)
