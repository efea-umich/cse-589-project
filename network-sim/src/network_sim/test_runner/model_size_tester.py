import jiwer

from collections import defaultdict

from tqdm import tqdm
from dataset import VoiceDataset
from sklearn.metrics import accuracy_score

from whisper.normalizers import EnglishTextNormalizer
from auto_vtt.speech_to_text import SpeechToTextConverter

class ModelSizeTester:
    def __init__(self, model_size: SpeechToTextConverter.ModelSize, dataset: VoiceDataset):
        self.model_size = model_size
        self.dataset = dataset
        self.stt = SpeechToTextConverter(model_size)
        
    def evaluate_model_size(self):
        results = defaultdict(list)
        normalize = EnglishTextNormalizer()
        
        for audios, transcription in tqdm(self.dataset):
            for noise_type, audio in audios.items():
                text = self.stt.transcribe(audio)
                results[noise_type].append(jiwer.wer(normalize(transcription), normalize(text)))
            
        results = {k: sum(v) / len(v) for k, v in results.items()}
        return results