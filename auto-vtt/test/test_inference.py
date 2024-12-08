import os

import pytest
import openai
import os

from src.auto_vtt.inferencing.action_classifier import ActionClassifier


# OpenAI fixture
@pytest.fixture
def gpt4o():
    client = openai.Client(api_key=os.environ.get("OPEN_AI_KEY"))

    def infer(prompt):
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Your task is to determine the action and object of the following command. Return the action and object in the format 'action:object'. For example, and output might be play:music",
                },
                {
                    "role": "system",
                    "content": "The possible actions are 'play', 'stop', and 'skip'. The possible objects are 'music', 'navigation', and 'news'.",
                },
                {"role": "user", "content": prompt},
            ],
            model="gpt-4o",
            timeout=5,
        )

        return response.choices[0].message.content

    return infer


def test_action_classifier():
    candidate_labels = ["music", "navigation", "news"]
    classifier = ActionClassifier(candidate_labels)

    sequence_to_classify = "Drive me to work"
    label, score = classifier(sequence_to_classify)
    assert label == "navigation"

    sequence_to_classify = "Play some pop"
    label, score = classifier(sequence_to_classify)
    assert label == "music"


def test_multi_level_classification():
    object_labels = ["music", "navigation", "news"]
    action_labels = ["play", "stop", "skip"]

    object_classifier, action_classifier = (
        ActionClassifier(object_labels),
        ActionClassifier(action_labels),
    )
    sequence_to_classify = "Put on the latest Taylor Swift album"

    object_label, object_score = object_classifier(sequence_to_classify)
    assert object_label == "music"

    action_label, action_score = action_classifier(sequence_to_classify)
    assert action_label == "play"


def test_openai_inference(gpt4o):
    prompt = "Play some music"
    response = gpt4o(prompt)
    assert response == "play:music"

    prompt = "Skip the current song"
    response = gpt4o(prompt)
    assert response == "skip:music"
