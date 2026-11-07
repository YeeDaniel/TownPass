import json
import sys

d = sys.argv[1]
layers = json.load(open(f"{d}/layers.json"))
html = open(f"{d}/template.html", encoding="utf-8").read().replace("__LAYERS__", json.dumps(layers))
out = f"{d}/taipei_station_stack.html"
open(out, "w", encoding="utf-8").write(html)
print("ok", out, len(html) // 1024, "KB")
