import math, numpy as np
def vp(az):
    ca, sa = math.cos(math.radians(az)), math.sin(math.radians(az))
    return lambda r, z: np.array([r*ca, r*sa, z])
def arc(pt, rc, zc, R, a0, a1, n=8):
    return [pt(rc + R*math.cos(math.radians(a0+(a1-a0)*k/n)), zc + R*math.sin(math.radians(a0+(a1-a0)*k/n))) for k in range(n+1)]
def segd(p1,q1,p2,q2):
    # min distance between segments, sampled
    best=1e9
    for t in np.linspace(0,1,41):
        a=p1+(q1-p1)*t
        d2=q2-p2; L=d2@d2
        u=np.clip(((a-p2)@d2)/L if L>0 else 0,0,1)
        best=min(best,np.linalg.norm(a-(p2+d2*u)))
    return best
def pd(A,B):
    return min(segd(A[i],A[i+1],B[j],B[j+1]) for i in range(len(A)-1) for j in range(len(B)-1))
def rot(pts,deg):
    c,s=math.cos(math.radians(deg)),math.sin(math.radians(deg))
    return [np.array([c*p[0]-s*p[1], s*p[0]+c*p[1], p[2]]) for p in pts]
BUS_R, BR = 1.4, 3.0
zl=48.0
vb, vl = vp(35), vp(235)
jxy=(7*math.cos(math.radians(35)), 7*math.sin(math.radians(35)))
lbj=vl(4,70)
import sys
legr=float(sys.argv[1]) if len(sys.argv)>1 else 6.0
axz=float(sys.argv[2]) if len(sys.argv)>2 else 64.0
# launcher static (near hub part): end -> inner leg -> U (centre r rc, radius R) -> riser r16 z68
R=(16-legr)/2; rc=legr+R
lb=[lbj, vl(legr, 66)] + arc(vl, rc, zl, R, 180, 360, 10) + [vl(16,68)]
# old launcher for reference
lb_old=[lbj, vl(3,66)] + arc(vl, 9.5, zl, 6.5, 180, 360, 10) + [vl(16,68)]
# bus static near-hub part: arch + U + inner leg -> axis end
bus=[vb(14,18)] + arc(vb,11.5,60,2.5,0,180,6) + arc(vb,6,zl,3,0,-180,8) + [vb(3,axz-4), np.array([0,0,axz])]
tail=[np.array([0,0,axz]), vb(3.5,axz+3), vb(7,axz+5), np.array([jxy[0],jxy[1],74.0])]
print("legr",legr,"axz",axz)
print("static bus vs static launcher gap", round(pd(bus,lb)-BUS_R-BR,2))
worst=(1e9,None)
for p in np.arange(-92.5,92.6,2.5):
    t=rot(tail,p)
    g=pd(t,lb)-BUS_R-BR
    g2=pd(t,bus[:-2])-2*BUS_R   # tail vs bus arch/U (not the joint end)
    if g<worst[0]: worst=(g,p)
    if abs(p) in (90,92.5,0) : print(" pan",p,"tail-launcher",round(g,2),"tail-busloop",round(g2,2))
print("worst tail-launcher", round(worst[0],2), "at", worst[1])
print("tail length", round(sum(np.linalg.norm(tail[i+1]-tail[i]) for i in range(len(tail)-1)),1))
