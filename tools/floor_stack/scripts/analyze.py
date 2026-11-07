import cv2, numpy as np, sys
S = sys.argv[1]
for f in ["b1","b2","b3","b4"]:
    im = cv2.imread(f"{S}/{f}.png")
    h, w = im.shape[:2]
    b, g, r = [im[:,:,i].astype(int) for i in range(3)]
    red = ((r > 180) & (g < 80) & (b < 80)).astype(np.uint8)
    # dots: red blobs that survive opening (lines are thin)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
    dots = cv2.morphologyEx(red, cv2.MORPH_OPEN, k)
    n, lab, st, cen = cv2.connectedComponentsWithStats(dots)
    pts = [(int(cen[i][0]), int(cen[i][1]), int(st[i][4])) for i in range(1,n) if 15 < st[i][4] < 400 and 230 < cen[i][1] < 1500]
    # light-blue footprint bbox
    lb = ((b > 240) & (g > 238) & (r > 225) & (r < 245) & (b - r > 8)).astype(np.uint8)
    ys, xs = np.nonzero(lb[230:1500]); 
    print(f, w, h, "footprint bbox", xs.min(), ys.min()+230, xs.max(), ys.max()+230)
    print("  dots", sorted(pts, key=lambda p:(p[1],p[0])))
