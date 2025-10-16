import cv2
from matplotlib import pyplot as plt
import os

IMG_PATH = os.path.join('images', '1.jpg')
img = cv2.imread(IMG_PATH)

if img is None:
    print("❌ تصویر پیدا نشد:", IMG_PATH)
else:
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # چون OpenCV رنگ‌ها رو برعکس نشون میده
    plt.imshow(img_rgb)
    plt.title('My Image')
    plt.axis('off')  # حذف محور‌ها
    plt.show()
