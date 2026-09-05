"""Download the local multilingual transcription model once."""
from faster_whisper import WhisperModel
model=WhisperModel('base',device='cpu',compute_type='int8')
print('Whisper base model is cached and ready for offline media transcription.')
