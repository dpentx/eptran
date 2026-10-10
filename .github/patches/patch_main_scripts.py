"""Workflow'lara 'scriptleri main'den calistir' degisikligini uygular.
Kullanim: python patch_main_scripts.py <repo-dizini>"""
import os
import sys

NL = chr(10)
target = sys.argv[1]
wf_dir = os.path.join(target, ".github", "workflows")
FILES = ["translate.yml", "queue-worker.yml", "review.yml", "qa.yml", "convert.yml", "pr-check.yml"]

SYNC_STEP = [
    "      # Kod HER ZAMAN main'den gelir; dal sadece veri (status.json, output/ ...)",
    "      # tasir. Aksi halde dal acildigi andaki eski script'lerle calisir, main'e",
    "      # giren duzeltmeler acik kitaplara ulasmaz (ve bir PR'in kendi pr_check.py'sini",
    "      # degistirerek kontrolu zayiflatmasi mumkun olur).",
    "      - name: Use scripts from main",
    "        run: |",
    "          git fetch origin main",
    '          mkdir -p "$RUNNER_TEMP/main-code"',
    '          git archive FETCH_HEAD scripts requirements.txt | tar -x -C "$RUNNER_TEMP/main-code"',
    '          echo "MAIN_CODE=$RUNNER_TEMP/main-code" >> "$GITHUB_ENV"',
]


def patch(text):
    assert "MAIN_CODE" not in text, "zaten yamali"
    lines = text.split(NL)
    ci = next(i for i, ln in enumerate(lines) if "uses: actions/checkout@v4" in ln)
    j = ci + 1
    while j < len(lines) and not lines[j].startswith("      - name:"):
        j += 1
    assert j < len(lines), "checkout sonrasi adim bulunamadi"
    k = j
    while k - 1 > ci and (lines[k - 1].strip() == "" or lines[k - 1].lstrip().startswith("#")):
        k -= 1
    lines[k:k] = [""] + SYNC_STEP
    out = NL.join(lines)
    assert "pip install -r requirements.txt" in out
    out = out.replace("pip install -r requirements.txt", 'pip install -r "$MAIN_CODE/requirements.txt"')
    marker = "python scripts/"
    pos = 0
    while True:
        p = out.find(marker, pos)
        if p < 0:
            break
        start = p + len(marker)
        end = start
        while end < len(out) and out[end] not in " " + NL + '"':
            end += 1
        out = out[:p] + 'python "$MAIN_CODE/scripts/' + out[start:end] + '"' + out[end:]
        pos = p + 1
    return out


for name in FILES:
    path = os.path.join(wf_dir, name)
    text = open(path, encoding="utf-8").read()
    open(path, "w", encoding="utf-8").write(patch(text))
    print("patched", name)
