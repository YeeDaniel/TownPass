import cv2, numpy as np, sys, json, base64
S = sys.argv[1]
def yellow_extent(f, y0, y1):
    im = cv2.imread(f"{S}/{f}.png"); b,g,r = [im[y0:y1,:,i].astype(int) for i in range(3)]
    m = (r > 230) & (g > 180) & (b < 90); xs = np.nonzero(m)[1]; ys = np.nonzero(m)[0] + y0
    return xs.min(), xs.max(), int(np.median(ys))
print("B1 band", yellow_extent("b1", 1255, 1335))
print("B2 band", yellow_extent("b2", 1290, 1395))
