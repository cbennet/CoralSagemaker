import argparse
import platform
import subprocess
from edgetpu.detection.engine import DetectionEngine
from PIL import Image
from PIL import ImageDraw
import cscore
import numpy as np
from time import time

WIDTH, HEIGHT = 320, 240


# 0.0017*w**2-0.3868*w+26.252
# Distance? =(((x1 + x2)/2-160)/((x1 - x2)/19.5))/12
# Angle =(9093.75/POWER(E5-D5, LOG(54/37,41/29)))/12
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--model', help='Path of the detection model.', required=True)
    args = parser.parse_args()

    # Initialize engine.
    engine = DetectionEngine(args.model)
    labels = {0: "hatch",
              1: "cargo"}

    cs = cscore.CameraServer.getInstance()
    camera = cs.startAutomaticCapture()
    camera.setResolution(WIDTH, HEIGHT)
    cvSink = cs.getVideo()
    img = np.zeros(shape=(HEIGHT, WIDTH, 3), dtype=np.uint8)

    output = cs.putVideo("MLOut", WIDTH, HEIGHT)

    start = time()
    # Open image.
    while True:
        t, img = cvSink.grabFrame(img)
        frame = Image.fromarray(img)
        draw = ImageDraw.Draw(frame)

        # Run inference.
        ans = engine.DetectWithImage(frame, threshold=0.05, keep_aspect_ratio=True, relative_coord=False, top_k=10)

        # Display result.
        if ans:
            for obj in ans:
                print('-----------------------------------------')
                if labels:
                    print(labels[obj.label_id])
                print('score = ', obj.score)
                box = obj.bounding_box.flatten().tolist()
                x1, y1, x2, y2 = box
                print(abs(x1 - x2))
                print('box = ', box)
                # Draw a rectangle.
                draw.rectangle(box, outline='green')
                output.putFrame(np.array(frame))
        else:
            print('No object detected!')
            output.putFrame(img)
        print("FPS:", 1 / (time() - start))

        start = time()


if __name__ == '__main__':
    main()
