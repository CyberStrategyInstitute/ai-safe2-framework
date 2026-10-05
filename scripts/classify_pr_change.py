import os

with open(os.environ["GITHUB_OUTPUT"], "a") as f:
    f.write("route=solution\n")
