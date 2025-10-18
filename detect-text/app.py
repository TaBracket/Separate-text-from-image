import cv2
import os
# Load Image
# import matplotlib for viz
from matplotlib import pyplot as plt
# define the file path to the image
IMG_PATH = os.path.join("images", "1.jpg")
# Read in image
img = cv2.imread(IMG_PATH)
# Resize image
resized_img = cv2.resize(img , (int(img.shape[1]/4) , int(img.shape[0]/4)))
# Edge detection using Canny
gray = cv2.cvtColor(resized_img,cv2.COLOR_BGR2GRAY)
blur = cv2.GaussianBlur(gray,(5,5),0 )
canny = cv2.Canny(blur, threshold1=100, threshold2=100)
# view image using opencv
cv2.imshow('img',canny)
cv2.waitKey(0)
cv2.destroyAllWindows()