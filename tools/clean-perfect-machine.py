# Makes assets/perfect-machine-clean.jpg from Katia's original "perfect machine" drawing
# (03-original-art/earlier-concepts/image-6.png) with the orange "i am a perfect machine!.." text removed.
# The original file is never modified.
import cv2, numpy as np
im=cv2.imread("../03-original-art/earlier-concepts/image-6.png")
H,W=im.shape[:2]
b,g,r=[im[...,i].astype(int) for i in range(3)]
orange=((r>150)&(r-b>70)&(g>70)&(r-g>20)).astype(np.uint8)*255
orange[:int(H*0.8)]=0                                  # the caption only lives in the bottom band
ys,xs=np.nonzero(orange); y0,y1,x0,x1=ys.min()-14,ys.max()+16,xs.min()-18,xs.max()+18
mask=np.zeros((H,W),np.uint8); mask[y0:y1,x0:x1]=255     # whole caption box, so the letters' dark outline goes too
out=cv2.inpaint(im,mask,25,cv2.INPAINT_TELEA)
# the drawing is soft-focus here: blur the repaired box and feather it back in
soft=cv2.GaussianBlur(out,(0,0),9)
f=np.zeros((H,W),np.float32); f[y0-20:y1+20,x0-30:x1+30]=1; f=cv2.GaussianBlur(f,(0,0),12)[...,None]
out=(out*(1-f)+soft*f).astype(np.uint8)
cv2.imwrite("assets/perfect-machine-clean.jpg",out,[cv2.IMWRITE_JPEG_QUALITY,90])
print(W,H,int((orange>0).sum()),"caption pixels removed")
