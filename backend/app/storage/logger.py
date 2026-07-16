import json
import os
import time
import uuid


class GameLogger:
    def __init__(self, path="game_logs/random"):
        os.makedirs(path, exist_ok=True)
        self.game_id = str(uuid.uuid4())
        self.filepath = os.path.join(path, f"{self.game_id}.jsonl")
        self.file = open(self.filepath, "w")

    def log(self, event_type, **details):
        event = {
            "game_id": self.game_id,
            "timestamp": time.time(),
            "event_type": event_type,
        }
        event.update(details)
        self.file.write(json.dumps(event) + "\n")
        self.file.flush()   # force it out of the buffer onto disk immediately

    def close(self):
        self.file.close()