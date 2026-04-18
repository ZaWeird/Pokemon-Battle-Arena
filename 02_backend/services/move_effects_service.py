import random

def calculate_move_accuracy(move):
    accuracy = move.get('accuracy', 100)
    if accuracy is None or accuracy == 0:
        return True
    return random.randint(1, 100) <= accuracy