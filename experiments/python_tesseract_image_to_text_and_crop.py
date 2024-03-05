from PIL import Image
import pytesseract
import os
import concurrent.futures
from pdf2image import convert_from_path
import cv2
import numpy as np
 
pdf_of_images = '/Users/jamescourson/Documents/scripts/image-to-text/The Manner of Special Revelation.pdf'
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'
directory = 'images'
confirmed_filenames = []


def crop_percentage(image, percent=8):
    """
    Crop the given percentage from the edges of an image.

    Params:
    - image: pre-loaded image array
    - percent: percentage of the edge to crop

    Returns:
    - cropped image array
    """
    h, w = image.shape[:2]
    h_crop = int(h * percent / 100)
    w_crop = int(w * percent / 100)

    return image[h_crop:-h_crop, w_crop:-w_crop]

def find_crop_boundaries(image, depth_percent_top=3, depth_percent_bottom=2, threshold_top=.15, threshold_bottom=0.2):
    """
    Find crop boundaries based on pixel density.

    Params:
    - image: pre-loaded image array
    - depth_percent: percentage of the image height to use as depth for calculating pixel density
    - threshold: density threshold to determine cropping boundary

    Returns:
    - y_start, y_end: vertical cropping boundaries
    """

    # Convert to grayscale if it's not
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Threshold the image to binary using Otsu's method
    _, bin_img = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    h, w = bin_img.shape

    # Calculate depth in pixels from the percentage
    depth_top = int(h * depth_percent_top / 100)
    depth_bottom = int(h * depth_percent_bottom / 100)

    # Scanning from the top
    y_start = 0
    for y in range(0, h - depth_top):
        density = np.sum(bin_img[y:y+depth_top, :]) / (255.0 * w * depth_top)
        if density > threshold_top:
            y_start = y
            break

    # Scanning from the bottom
    y_end = h - 1
    for y in range(h - 1, depth_bottom, -1):
        density = np.sum(bin_img[y-depth_bottom:y, :]) / (255.0 * w * depth_bottom)
        if density > threshold_bottom:
            y_end = y
            break

    return y_start, y_end


def convert_pdf_to_images(pdf_path):
    return convert_from_path(pdf_path)

def preprocess(image_path):

    opencv_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    opencv_image = crop_percentage(opencv_image, 5)

    y_start, y_end = find_crop_boundaries(opencv_image)

    # Crop and save the image
    opencv_image = np.array(images[0])
    cropped_image = opencv_image[y_start:y_end, :]
    image_rgb = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)

    # Convert to a PIL Image
    image_pil = Image.fromarray(image_rgb)

    return image_pil

# helper function to process images
def process_image(filename):
    # preprocessed_img = preprocess(filename)

    # print(f'Preprocessed: {filename}')
    # #saved processed image
    # preprocessed_img.save('processed/' + filename.split('/')[-1])

    # image_from_text = pytesseract.image_to_string(preprocessed_img)
    image_from_text = pytesseract.image_to_string(Image.open(filename))
    return image_from_text



# def display_image_opencv(img, convert_bgr_to_rgb=True):
#     """Convert an OpenCV image to RGB and display it in Jupyter."""
#     if convert_bgr_to_rgb:
#         img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#     img_pil = PILImage.fromarray(img)
#     display(img_pil)







print(f'Pulling images from: {pdf_of_images}')
images = convert_pdf_to_images(pdf_of_images)

save_names = []
for i in range(len(images)):
    save_name = 'images/page'+ str(i) +'.jpg'
    save_names.append(save_name)
    images[i].save(save_name, 'JPEG') # Save pages as images in the pdf

print(f'Images saved to: {directory}')

for filename in save_names:
    f = os.path.join(filename)

    if os.path.isfile(f):
        confirmed_filenames.append(f)

print(confirmed_filenames)

with concurrent.futures.ThreadPoolExecutor(max_workers=9) as executor:
    results = list(executor.map(process_image, confirmed_filenames))

   
text = ' '.join(results)
# ^\n+$ remove 
# ^\d+$
# (?<=[a-zA-Z-])\n 
# (?<=\b(?:Gen|Exod|Lev|Num|Deut|Josh|Judg|Ruth|1\s*Sam|2\s*Sam|1\s*Kin|2\s*Kin|1\s*Chron|2\s*Chron|Ezra|Neh|Esth|Job|Ps|Prov|Eccles|Song\s*of\s*Sol|Isa|Jer|Lam|Ezek|Dan|Hos|Joel|Amos|Obad|Jonah|Mic|Nah|Hab|Zeph|Hag|Zech|Mal|Matt|Mark|Luke|John|Acts|Rom|1\s*Cor|2\s*Cor|Gal|Eph|Phil|Col|1\s*Thess|2\s*Thess|1\s*Tim|2\s*Tim|Titus|Philemon|Heb|James|1\s*Pet|2\s*Pet|1\s*John|2\s*John|3\s*John|Jude|Rev))\.


with open('output.txt', 'a') as f:
    f.write(text)
