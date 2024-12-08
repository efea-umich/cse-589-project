from transformers import pipeline
import torch

classifier = pipeline(
    "zero-shot-classification", model="MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
)


class ActionClassifier:
    def __init__(self, labels):
        self.labels = labels
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def __call__(self, sequence_to_classify: str) -> tuple[str, float]:
        out = classifier(sequence_to_classify, self.labels)
        return (out["labels"][0], out["scores"][0])
