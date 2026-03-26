import sys
import json
while True:
    data = sys.stdin.readline()
    print(json.dumps({"move": "DOWN"}))
    sys.stdout.flush()
