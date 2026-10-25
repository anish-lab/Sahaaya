"""Stage, commit, merge to main, and push to origin and pgit."""
import subprocess
import sys

def run(cmd):
    print(f">> {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr:
        print(res.stderr.strip())
    if res.returncode != 0:
        print(f"[FAIL] Command failed with code {res.returncode}")
        sys.exit(res.returncode)

run("git add .")
commit_msg = "Validate vulnerability index vs NITI Aayog MPI (rho=0.9037), justify weights, add clustering rigor, honest simulator, CI, and align README"
run(f'git commit -m "{commit_msg}"')

# Push ui-redesign
run("git push origin ui-redesign")
run("git push pgit ui-redesign")

# Switch to main and merge
run("git checkout main")
run("git merge ui-redesign")
run("git push origin main")
run("git push pgit main")

# Switch back to ui-redesign
run("git checkout ui-redesign")
print("All branches successfully updated and pushed!")
