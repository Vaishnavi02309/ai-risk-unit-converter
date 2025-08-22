import os, re, json, subprocess, sys, pathlib, yaml
from typing import List
from gemini_client import ask_gemini

ROOT = pathlib.Path(__file__).resolve().parents[1]

def run(cmd: List[str]) -> str:
    return subprocess.check_output(cmd, cwd=ROOT, text=True, stderr=subprocess.STDOUT)

def get_diff(base_ref: str, head_ref: str) -> str:
    run(["git", "fetch", "origin", base_ref, "--depth=1"])
    return run(["git", "diff", "--unified=0", f"origin/{base_ref}...{head_ref}"])

def parse_changed_files(diff_text: str):
    files = []
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                files.append(parts[3][2:])  # strip b/
    return sorted(set(files))

def count_changed_lines(diff_text: str) -> int:
    total = 0
    for l in diff_text.splitlines():
        if l.startswith("+") and not l.startswith("+++"): total += 1
        if l.startswith("-") and not l.startswith("---"): total += 1
    return total

def file_risk_weight(path: str, path_weights: dict) -> int:
    score = 0
    for pat, wt in path_weights.items():
        if re.search(pat, path):
            score = max(score, wt)
    return score

def keyword_risk(diff_text: str, patterns):
    s = 0
    for item in patterns:
        if re.search(item["pattern"], diff_text, flags=re.IGNORECASE|re.MULTILINE):
            s += int(item["weight"])
    return s

def band_label(score: int, bands: dict) -> str:
    if score <= int(bands["low"]["max"]): return "low"
    if score <= int(bands["medium"]["max"]): return "medium"
    return "high"

def main():
    ev = json.load(open(os.getenv("GITHUB_EVENT_PATH"), "r", encoding="utf-8"))
    base_ref = ev["pull_request"]["base"]["ref"]
    head_sha = ev["pull_request"]["head"]["sha"]

    rules = yaml.safe_load(open(ROOT/"risk"/"rules.yml", "r", encoding="utf-8"))
    diff = get_diff(base_ref, head_sha)
    files = parse_changed_files(diff)
    lines = count_changed_lines(diff)
    touched_tests = any(re.match(r"tests/.*\\.py$", f) for f in files)

    th = rules["size_thresholds"]
    size_score = 0 if lines <= th["small"] else 1 if lines <= th["medium"] else 3
    path_score = sum(file_risk_weight(f, rules["path_weights"]) for f in files)
    kw_score   = keyword_risk(diff, rules["hunk_keywords"])
    base_score = size_score + path_score + kw_score

    ai_delta, ai_expl = 0, "AI adjustment disabled or no API key."
    if rules["ai_adjustment"]["enabled"] and os.getenv("GEMINI_API_KEY"):
        short_diff = "\n".join(diff.splitlines()[:400])
        prompt = (
            "You are a CI risk assistant for a tiny unit converter library "
            "(length: m/km/cm/mm; weight: g/kg). "
            "Given this unified diff, classify overall change risk as LOW/MEDIUM/HIGH "
            "and explain briefly (one short paragraph). DIFF:\n" + short_diff
        )
        ai_text = ask_gemini(prompt)
        max_delta = int(rules["ai_adjustment"]["max_delta"])
        low = ai_text.lower()
        if "high" in low: ai_delta = min(2, max_delta)
        elif "medium" in low: ai_delta = min(1, max_delta)
        elif "low" in low: ai_delta = max(-1, -max_delta)
        ai_expl = ai_text.strip()

    total = max(0, base_score + ai_delta)
    band = band_label(total, rules["risk_bands"])
    gate_fail = (band == "high" and rules["gate_policy"]["require_tests_on_high_risk"] and not touched_tests)

    report = f"""### 🤖 AI Risk Score

- **Risk band:** **{band.upper()}** (score={total}, base={base_score}, ai_delta={ai_delta})
- **Changed files:** {', '.join(files) if files else '—'}
- **Changed lines:** {lines}
- **Tests touched:** {"yes" if touched_tests else "no"}

**Rule-based signals**
- Path score: {path_score}
- Keyword score: {kw_score}
- Size score: {size_score}

**AI note**
> {ai_expl[:800]}

{"❗ **Gate**: High risk without test changes — failing check." if gate_fail else "✅ Gate: OK"}
"""
    # Post PR comment
    import urllib.request
    repo = os.getenv("GITHUB_REPOSITORY")
    pr_number = ev["number"]
    api = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    req = urllib.request.Request(api, method="POST",
        data=json.dumps({"body": report}).encode())
    req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    req.add_header("Accept", "application/vnd.github+json")
    urllib.request.urlopen(req).read()

    if gate_fail:
        print("Gate failed: High risk without tests.")
        sys.exit(2)

if __name__ == "__main__":
    main()
