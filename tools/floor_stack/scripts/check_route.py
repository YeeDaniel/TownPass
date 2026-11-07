import cv2, sys
S = sys.argv[1]
pts = {"b1":[(800,1150),(790,1290),(652,1305),(720,1292),(820,1100),(835,1180)],
       "b2":[(640,1338),(925,1330),(955,1250),(988,1095),(970,1180)],
       "b4":[(1030,960),(1075,760),(1010,1000),(1050,880)]}
for f, ps in pts.items():
    im = cv2.imread(f"{S}/{f}.png")
    for x,y in ps:
        b,g,r = im[y,x]; print(f, (x,y), "rgb", (int(r),int(g),int(b)), "YELLOW" if r>230 and g>180 and b<90 else "")
