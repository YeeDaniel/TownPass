import cv2, numpy as np, sys, base64, json
S, OUT = sys.argv[1], sys.argv[2]
SCALE = 0.75
res = {}
for f in ["b1","b2","b3","b4"]:
    im = cv2.imread(f"{S}/{f}.png").astype(np.float32)
    h, w = im.shape[:2]
    mn = im.min(axis=2)
    a = np.clip((255 - mn) / 45.0, 0, 1)
    a[:222, :] = 0; a[1496:, :] = 0            # header bar, legend
    a[255:370, 30:490] = 0                      # floor title
    a[235:365, 1290:1400] = 0                   # compass
    safe = np.maximum(a, 1e-3)[..., None]
    col = np.clip((im - (1 - a[..., None]) * 255) / safe, 0, 255)
    rgba = np.dstack([col, a * 255]).astype(np.uint8)
    small = cv2.resize(rgba, (int(w*SCALE), int(h*SCALE)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".webp", small, [cv2.IMWRITE_WEBP_QUALITY, 90])
    ys, xs = np.nonzero(a > 0.25)
    res[f] = {"w": w, "h": h, "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
              "uri": "data:image/webp;base64," + base64.b64encode(buf.tobytes()).decode()}
    print(f, "bbox", res[f]["bbox"], "webp KB", len(buf)//1024)
json.dump(res, open(OUT, "w"))
