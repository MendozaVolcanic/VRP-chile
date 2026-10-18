import sys
sys.path.insert(0, sys.argv[1])
import cv2
import ocr_utils
for f, vol in [(a.split('::')[0], a.split('::')[1]) for a in sys.argv[2:]]:
    img = cv2.imread(f)
    print(f.split('/')[-1], vol, '->', ocr_utils.validar_con_estrella_verde(img, vol))
