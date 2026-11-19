import subprocess
import sys
import time


print("=== PROCESS CONTROL LAB ===")

process = subprocess.Popen(
    [
        sys.executable,
        "-c",
        "import time; time.sleep(5); print('Child finished')"
    ]
)

print("PID:", process.pid)

print("Initial status:", process.poll())

time.sleep(2)

print("Status after 2 seconds:", process.poll())

print("Terminating process...")

process.terminate()

exit_code = process.wait()

print("Final exit code:", exit_code)

print("Final status:", process.poll())

print("=== LAB COMPLETE ===")


import subprocess
import sys

result = subprocess.run(
    [
        sys.executable,
        "-c",
        (
            "import sys; "
            "print('Normal output'); "
            "print('Diagnostic output', file=sys.stderr); "
            "sys.exit(0)"
        )
    ],
    capture_output=True,
    text=True,
    timeout=5,
    check=False
)

print("STDOUT:", result.stdout.strip())
print("STDERR:", result.stderr.strip())
print("EXIT CODE:", result.returncode)