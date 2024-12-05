from src.auto_vtt.inferencing.action_classifier import ActionClassifier

def test_action_classifier():
    candidate_labels = ['music', 'navigation', 'news']
    classifier = ActionClassifier(candidate_labels)

    sequence_to_classify = "Drive me to work"
    label, score = classifier(sequence_to_classify)
    assert label == "navigation"

    sequence_to_classify = "Play some pop"
    label, score = classifier(sequence_to_classify)
    assert label == "music"
