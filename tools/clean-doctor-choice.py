# Makes assets/doctor-choice-clean.jpg from Katia's original doctor-dialogue drawing
# (03-original-art/earlier-concepts/image-10.png) with the baked-in option bars and
# "choose. it's safe" subtitle removed. The original file is never modified.
import cv2, numpy as np
im=cv2.imread("../03-original-art/earlier-concepts/image-10.png")[:1256].astype(np.float32)
H,W=im.shape[:2]; y0,y1=630,1066; X=np.arange(W)
coat=lambda y: 1080+(y-825)*0.716 if y>=825 else 0     # right edge of the Doctor's coat per row
def edge_row(rows):
    r=rows.mean(0).clip(0,255).astype(np.uint8)
    seg=r[1250:].reshape(1,-1,3)
    r[1250:]=cv2.medianBlur(seg,41)[0]                  # wipe thin lines (panel edges) out of the reference rows
    return r.astype(np.float32)
top=edge_row(im[y0-6:y0-1]); bot=edge_row(im[y1+1:y1+6])
out=im.copy()
for y in range(y0,y1):
    t=(y-y0)/(y1-y0); fill=top*(1-t)+bot*t              # background rebuilt as a vertical gradient
    xl=int(max(1236, coat(y)+14))
    L=np.percentile(im[max(y-12,0):y+12,xl-12:xl-2].reshape(-1,3),80,axis=0)  # glow left of the bars, ignoring dark coat strokes
    corr=(L-fill[xl]).copy()
    w=np.clip(1-(X-xl)/300,0,1); w=w*w*(3-2*w)          # carry the glow's brightness in, fading over 300px
    fill=fill+corr[None,:]*w[:,None]
    a=np.clip((X-(xl-6))/12,0,1)[:,None]
    out[y]=im[y]*(1-a)+fill*a
for yy in (y0,y1):
    out[yy-8:yy+8,1200:]=cv2.GaussianBlur(out[yy-8:yy+8,1200:],(1,15),0)
out[:,W-8:]=out[:,W-9:W-8]
out=out.clip(0,255).astype(np.uint8)
b,g,r=[out[...,i].astype(int) for i in range(3)]
orange=((r>140)&(r-b>50)&(g>80)&(r-g<120)).astype(np.uint8)*255; orange[:1100]=0
out=cv2.inpaint(out,cv2.dilate(orange,np.ones((11,11),np.uint8),2),9,cv2.INPAINT_TELEA)
cv2.imwrite("assets/doctor-choice-clean.jpg",out,[cv2.IMWRITE_JPEG_QUALITY,90])
