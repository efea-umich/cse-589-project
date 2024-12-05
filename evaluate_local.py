import tarfile
from pathlib import Path
import pandas as pd
from tqdm import tqdm
import torch
from torchmetrics import Accuracy, F1Score, AUROC

from src.auto_vtt.audio_processing import AudioProcessor
from src.auto_vtt.speech_to_text import SpeechToTextConverter
from src.auto_vtt.inferencing.action_classifier import ActionClassifier

# extract_path = Path(".")
# # Extract the tar.gz file - run only once!
# with tarfile.open("fluent.tar.gz", "r:gz") as tar:
#     tar.extractall(path=extract_path)

# Prepare evaluation data
y_true_action = []
y_pred_action = []
y_true_object = []
y_pred_object = []
y_true_location = []
y_pred_location = []

dataset_path = "fluent_speech_commands_dataset/data/test_data.csv"
df = pd.read_csv(dataset_path)
action_labels = list(df["action"].unique())
num_labels = len(action_labels)

audio_processor = AudioProcessor()
speech_to_text_converter = SpeechToTextConverter(SpeechToTextConverter.ModelSize.TINY)
action_classifier = ActionClassifier(labels=action_labels)

# Initialize metrics
accuracy_metric = Accuracy(task="multiclass", num_classes=num_labels)
f1_metric = F1Score(task="multiclass", num_classes=num_labels, average="macro")
auroc_metric = AUROC(task="multiclass", num_classes=num_labels)

noises = ["ac", "turnsignal", "convo"]

# using only first 10 rows of the dataset for now bc too slow
for _, row in tqdm(df.head(10).iterrows(), total=10):
    audio_path = row["path"]
    full_audio_path = f"dataset/fluent_speech_commands_dataset/{audio_path}"
    # looking only at action and not object inferences
    true_action = row["action"]

    tmp_dir = Path("tmpdir")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Process the audio
    processed_audios = audio_processor.process_file(full_audio_path)
    # for noisetype, processed_audio in processed_audios.items():
    for noise in noises:
        processed_audio = processed_audios[noise]
        processed_audio_path = tmp_dir / f"processed_audio_{noise}.wav"
        processed_audio.export(processed_audio_path, format='wav')
        # Step 2: Convert audio to text
        predicted_text = speech_to_text_converter.transcribe(processed_audio_path)

        # Step 3: Run inference
        if predicted_text:
            predicted_action, score = action_classifier(predicted_text)
            print(predicted_action, "  ", score)

            # Collect true and predicted labels for evaluation
            y_true_action.append(true_action)
            y_pred_action.append([predicted_action, score])

# convert string labels to numerical values
label_map = {}
for i, label in enumerate(action_labels):
    label_map[label] = i

y_true_mapped = [label_map[value] for value in y_true_action]
y_pred_mapped = [label_map[value[0]] for value in y_pred_action]

# Convert labels to tensors
y_true_tensor = torch.tensor(y_true_mapped)
y_pred_tensor = torch.tensor(y_pred_mapped)
y_pred_auroc = []
for pred_action, score in y_pred_action:
    curr_list = [(float(1-score)) / (num_labels - 1)]*num_labels
    curr_list[action_labels.index(pred_action)] = float(score)
    y_pred_auroc.append(curr_list)
auroc_pred_tensor = torch.tensor(y_pred_auroc)

# Evaluate metrics for actions
accuracy_action = accuracy_metric(y_pred_tensor, y_true_tensor)
f1_action = f1_metric(y_pred_tensor, y_true_tensor)
auroc_action = auroc_metric(auroc_pred_tensor, y_true_tensor)


# Print results
print("Action Classification Metrics:")
print(f"Accuracy: {accuracy_action:.2f}")
print(f"F1 Score: {f1_action:.2f}")
print(f"AUROC: {auroc_action:.2f}")
