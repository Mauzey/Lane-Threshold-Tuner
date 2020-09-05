# -*- coding: utf-8 -*-
# import
print('[INFO] Importing dependencies...')
from preprocessor import PreProcessor
import numpy as np
import cv2

# setup
print('[INFO] Setting up...')
cv2.namedWindow('LD Threshold Tuner') # initialise CV2 window
image_path = 'lane.jpeg'

# initialise pre-processor object
preproc = PreProcessor()

def mouse_event_handler(event, mouse_x, mouse_y, flags, param):
    """ Handles mouse events """
    if event == cv2.EVENT_MOUSEMOVE:
        # select ROI vertex when mouse is over it
        preproc.move_roi_vertex(mouse_x, mouse_y)
    elif event == cv2.EVENT_LBUTTONDBLCLK:
        # add ROI vertex at current position
        preproc.add_roi_vertex(mouse_x, mouse_y)
    elif event == cv2.EVENT_LBUTTONDOWN:
        # mark selected ROI vertex as active (if applicable)
        preproc.active_vtx_id = preproc.selected_vtx_id
    elif event == cv2.EVENT_LBUTTONUP:
        # mark active ROI vertex as inactive
        if preproc.active_vtx_id != -1:
            print('[INFO] Moved ROI vertex {} to position (x: {}, y: {})'.format(
                    preproc.active_vtx_id, mouse_x, mouse_y))
            preproc.active_vtx_id = -1
###

# initialise mouse event handler
cv2.setMouseCallback('LD Threshold Tuner', mouse_event_handler)

print('[INFO] Setup complete!')

if __name__ == '__main__':
    print('[INFO] Executing main sequence...')
    while(True):
        frame = cv2.imread(image_path)
        processed_frame = frame.copy()
        
        preproc.update(frame) # update pre-processor object
        processed_frame = preproc.process_frame(processed_frame) # apply preprocessing
        
        # place frames side-by-side and show the window
        combined_frame = np.hstack((frame, processed_frame))
        cv2.imshow('LD Threshold Tuner', combined_frame)
        
        # handling user input
        keypress = cv2.waitKey(20 & 0xFF)
        if keypress == ord('q'):
            print('[INFO] Closing application...')
            cv2.destroyAllWindows()
            break