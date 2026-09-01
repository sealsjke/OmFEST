import init_db
import subprocess


print("[+] Starting NFT Ducks")

init_db.initialize_database()

print("[+] Starting Flask")

subprocess.run(
    ["python", "app.py"],
    check=True
)