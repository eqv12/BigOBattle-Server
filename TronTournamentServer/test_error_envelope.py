import json
import os
import sys

# Change directory just in case
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from server.logic.engine import run_match

def create_bot(name, code):
    os.makedirs(f"bots/{name}", exist_ok=True)
    with open(f"bots/{name}/bot.py", "w") as f:
        f.write(code)
    with open(f"bots/{name}/run.sh", "w") as f:
        f.write("#!/bin/bash\npython3 bot.py")
    os.chmod(f"bots/{name}/run.sh", 0o755)
    return f"bots/{name}/bot.py"

timeout_bot = create_bot("fail_timeout", """import sys
import time
data = sys.stdin.readline()
time.sleep(5)
print('{"move": "UP"}')
""")

valid_bot = create_bot("pass_valid", """import sys
import json
while True:
    data = sys.stdin.readline()
    print(json.dumps({"move": "DOWN"}))
    sys.stdout.flush()
""")

print("Testing Timeout Envelope...")
res = run_match(timeout_bot, valid_bot)
replay = json.loads(res["replay"])
print("Winner:", res["winner"])
print("Termination:", res["termination_reason"])
print("Error Envelope:\n", json.dumps(replay["result"].get("error_envelope"), indent=2))
