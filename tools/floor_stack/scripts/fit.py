import numpy as np
src = np.array([(652,1305),(1071,1302),(1041,600),(523,1292),(1190,1292)], float)
dst = np.array([(621,1314),(1227,1296),(1188,385),(588,1281),(1278,1281)], float)
names = ["elev4","elev7","elev3","bandW","bandE"]
def fit(src, dst, sim):
    A, B = [], []
    for (x,y),(u,v) in zip(src,dst):
        if sim:
            A += [[x,-y,1,0],[y,x,0,1]]; B += [u,v]
        else:
            A += [[x,y,1,0,0,0],[0,0,0,x,y,1]]; B += [u,v]
    p = np.linalg.lstsq(np.array(A), np.array(B), rcond=None)[0]
    M = np.array([[p[0],-p[1],p[2]],[p[1],p[0],p[3]]]) if sim else p.reshape(2,3)
    return M
for sim in (True, False):
    M = fit(src, dst, sim)
    res = (np.c_[src, np.ones(len(src))] @ M.T) - dst
    print("similarity" if sim else "affine", np.round(M,4).tolist())
    for n,r in zip(names,res): print(f"   {n:6s} resid {r.round(1)}  |{np.hypot(*r):.0f}px|")
