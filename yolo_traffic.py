# yolo_traffic.py

import numpy as np
import imutils
import time
from scipy import spatial
import cv2
import os

# Vehicle classes to count
list_of_vehicles = ["bicycle", "car", "motorbike", "bus", "truck", "train"]

FRAMES_BEFORE_CURRENT = 10
inputWidth, inputHeight = 416, 416

labelsPath = "yolo-coco/coco.names"
weightsPath = "yolo-coco/yolov3.weights"
configPath = "yolo-coco/yolov3.cfg"
outputVideoPath = "output.mp4"

preDefinedConfidence = 0.35
preDefinedThreshold = 0.25
USE_GPU = 0

# Load labels
with open(labelsPath) as f:
    LABELS = f.read().strip().split("\n")

np.random.seed(42)
COLORS = np.random.randint(0, 255, size=(len(LABELS), 3), dtype="uint8")


def displayVehicleCount(frame, vehicle_count):
    cv2.putText(
        frame,
        "Detected Vehicles: " + str(vehicle_count),
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )


def displayFPS(start_time, num_frames):
    current_time = int(time.time())

    if current_time > start_time:
        print("FPS:", num_frames)
        num_frames = 0
        start_time = current_time

    return start_time, num_frames


def drawDetectionBoxes(idxs, boxes, classIDs, confidences, frame):
    if len(idxs) > 0:
        for i in idxs.flatten():
            x, y = boxes[i][0], boxes[i][1]
            w, h = boxes[i][2], boxes[i][3]

            color = [int(c) for c in COLORS[classIDs[i]]]

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

            text = "{}: {:.2f}".format(LABELS[classIDs[i]], confidences[i])

            cv2.putText(
                frame,
                text,
                (x, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )

            cv2.circle(frame, (x + w // 2, y + h // 2), 3, (0, 255, 0), -1)


def initializeVideoWriter(video_width, video_height, videoStream):
    sourceVideofps = videoStream.get(cv2.CAP_PROP_FPS)

    if sourceVideofps <= 0:
        sourceVideofps = 20

    fourcc = cv2.VideoWriter_fourcc(*"MJPG")

    return cv2.VideoWriter(
        outputVideoPath,
        fourcc,
        sourceVideofps,
        (video_width, video_height),
        True
    )


def boxInPreviousFrames(previous_frame_detections, current_box, current_detections):
    centerX, centerY, width, height = current_box
    dist = np.inf
    frame_num = 0
    coord = None

    for i in range(FRAMES_BEFORE_CURRENT):
        coordinate_list = list(previous_frame_detections[i].keys())

        if len(coordinate_list) == 0:
            continue

        temp_dist, index = spatial.KDTree(coordinate_list).query([(centerX, centerY)])

        if temp_dist < dist:
            dist = temp_dist
            frame_num = i
            coord = coordinate_list[index[0]]

    if dist > (max(width, height) / 2):
        return False

    current_detections[(centerX, centerY)] = previous_frame_detections[frame_num][coord]
    return True


def count_vehicles(idxs, boxes, classIDs, vehicle_count, previous_frame_detections, frame):
    current_detections = {}

    if len(idxs) > 0:
        for i in idxs.flatten():
            x, y = boxes[i][0], boxes[i][1]
            w, h = boxes[i][2], boxes[i][3]

            centerX = x + (w // 2)
            centerY = y + (h // 2)

            if LABELS[classIDs[i]] in list_of_vehicles:
                current_detections[(centerX, centerY)] = vehicle_count

                if not boxInPreviousFrames(
                    previous_frame_detections,
                    (centerX, centerY, w, h),
                    current_detections
                ):
                    vehicle_count += 1

                ID = current_detections.get((centerX, centerY))

                if list(current_detections.values()).count(ID) > 1:
                    current_detections[(centerX, centerY)] = vehicle_count
                    vehicle_count += 1

                cv2.putText(
                    frame,
                    str(ID),
                    (centerX, centerY),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    2
                )

    return vehicle_count, current_detections


def runYolo(inputVideoPath):
    print("[INFO] loading YOLO from disk...")

    if not os.path.exists(configPath):
        print("YOLO config file not found:", configPath)
        return

    if not os.path.exists(weightsPath):
        print("YOLO weights file not found:", weightsPath)
        return

    net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)

    if USE_GPU:
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

    layerNames = net.getLayerNames()

    # FIXED FOR NEW OPENCV
    ln = net.getUnconnectedOutLayers()
    ln = ln.flatten()
    ln = [layerNames[i - 1] for i in ln]

    videoStream = cv2.VideoCapture(inputVideoPath)

    if not videoStream.isOpened():
        print("Error opening video file")
        return

    video_width = int(videoStream.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(videoStream.get(cv2.CAP_PROP_FRAME_HEIGHT))

    previous_frame_detections = [{(0, 0): 0} for _ in range(FRAMES_BEFORE_CURRENT)]

    num_frames = 0
    vehicle_count = 0

    writer = initializeVideoWriter(video_width, video_height, videoStream)

    start_time = int(time.time())

    while True:
        num_frames += 1
        print("FRAME:", num_frames)

        boxes = []
        confidences = []
        classIDs = []

        start_time, num_frames = displayFPS(start_time, num_frames)

        grabbed, frame = videoStream.read()

        if not grabbed:
            break

        blob = cv2.dnn.blobFromImage(
            frame,
            1 / 255.0,
            (inputWidth, inputHeight),
            swapRB=True,
            crop=False
        )

        net.setInput(blob)
        layerOutputs = net.forward(ln)

        for output in layerOutputs:
            for detection in output:
                scores = detection[5:]
                classID = np.argmax(scores)
                confidence = scores[classID]

                if confidence > preDefinedConfidence:
                    box = detection[0:4] * np.array(
                        [video_width, video_height, video_width, video_height]
                    )

                    centerX, centerY, width, height = box.astype("int")

                    x = int(centerX - (width / 2))
                    y = int(centerY - (height / 2))

                    boxes.append([x, y, int(width), int(height)])
                    confidences.append(float(confidence))
                    classIDs.append(classID)

        idxs = cv2.dnn.NMSBoxes(
            boxes,
            confidences,
            preDefinedConfidence,
            preDefinedThreshold
        )

        drawDetectionBoxes(idxs, boxes, classIDs, confidences, frame)

        vehicle_count, current_detections = count_vehicles(
            idxs,
            boxes,
            classIDs,
            vehicle_count,
            previous_frame_detections,
            frame
        )

        displayVehicleCount(frame, vehicle_count)

        writer.write(frame)

        cv2.imshow("Traffic Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        previous_frame_detections.pop(0)
        previous_frame_detections.append(current_detections)

    print("[INFO] cleaning up...")

    writer.release()
    videoStream.release()
    cv2.destroyAllWindows()