import pandas as pd
from pathlib import Path
from tqpm import tqdm
import jiwer # need pip install jiwer
from whisper.normalizers import EnglishTextNormalizer

from src.auto_vtt.audio_processing import AudioProcessor
from src.auto_vtt.speech_to_text import SpeechToTextConverter
from src.auto_vtt.inferencing.action_classifier import ActionClassifier

audio_processor = AudioProcessor()
action_classifier = ActionClassifier(labels=action_labels)
normalizer = EnglishTextNormalizer()

dataset_path = "fluent_speech_commands_dataset/data/test_data.csv"
df = pd.read_csv(dataset_path)
num_audios = len(list(df["transcription"]))
test_segment = df.sample(frac=0.1, random_state=42)

processed = {} # {audio path: true text}
for _, row in tdqm(test_segment.iterrows(), total=len(test_segment)):
    audio_path = row["path"]
    full_audio_path = f"fluent_speech_commands_dataset/{audio_path}"
    true_transcription = row["transcription"]

    tmp_dir = Path("tmpdir")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # process audio
    noise_type = "turnsignal"
    processed_audios = audio_processor.process_file(full_audio_path)
    p_audio = processed_audios["turnsignal"]
    processed_audio_path = tmp_dir / f"processed_{audio_path}.wav"
    processed_audio.export(processed_audio_path, format='wav')

    processed[processed_audio_path] = true_transcription

wer_averages = {} # {model size: score}
for model_size in SpeechToTextConverter.ModelSize:
    speech_to_text_converter = SpeechToTextConverter(model_size.value)
    # transcribe
    wer_list = []
    for path, true_text in processed:
        predicted_text = speech_to_text_converter.transcribe(path)
        normalized_pred = normalizer(predicted_text)
        normalized_true = normalizer(true_text)

        wer = jiwer.wer(normalized_true, normalized_pred)
        wer_list.append(wer)
    wer_average = sum(wer_list) / len(wer_list)
    wer_averages[model_size] = wer_average

print(wer_averages)



