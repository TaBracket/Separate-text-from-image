import cv2
import os
from matplotlib import pyplot as plt
IMG_PATH = os.path.join('images', '1.jpg')
img = cv2.imread(IMG_PATH)
print(img)
# resize img
resized_img = cv2.resize(img,(int(img.shape[1]/8),int(img.shape[0]/8)))
# view image using openCv
cv2.imshow('frame view', resized_img)
cv2.waitKey(0)
cv2.destroyAllWindows()
print("Image shape:", img.shape)