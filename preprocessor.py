# -*- coding: utf-8 -*-
# import modules
import matplotlib.pyplot as plt
import numpy as np
import cv2

class PreProcessor():
    def __init__(self):
        self.roi_vertices = [] # vertices which define a region of interest
        self.selected_vtx_id = -1 # stores id of the vertex the mouse is over (-1 = None)
        self.active_vtx_id = -1 # stores the id of the active vertex
        
        self.sobel_k_size = 15 # kernel size for sobel operator
        
        # colour threshold values (min, max)
        self.sat_threshold = (113,255) # saturation threshold
        self.val_threshold = (234,255) # value threshold
        
        print('[INFO] Pre-processor initialised!')
    ###
    
    def add_roi_vertex(self, x_pos, y_pos):
        """ Adds a region of interest vertex at the provided coordinates """
        # store up to 4 vertices
        if len(self.roi_vertices) < 4:
            self.roi_vertices.append(np.array([x_pos, y_pos], dtype=np.int32))
            print('[INFO] Added ROI vertex {} at position (x: {}, y: {})'.format(len(self.roi_vertices) - 1, x_pos, y_pos))
    ###
    
    def draw_roi(self, frame):
        """ Draw the stored ROI to a given frame """
        # fill as a polygon if there are 4 vertices
        if len(self.roi_vertices) >= 4:
            polygon_frame = frame.copy()
            cv2.fillPoly(polygon_frame, np.array([self.roi_vertices]), (255, 255, 255))
            cv2.addWeighted(frame, 0.8, polygon_frame, 0.2, 0.0, frame)
            
        # draw points and positional information for each set of coordinates
        for i, (x_pos, y_pos) in enumerate(self.roi_vertices):
            text_x, text_y = x_pos + 5, y_pos - 5 # text is above and to the side
            
            # if the mouse is over the current vertex, colour it red
            if i == self.selected_vtx_id:
                cv2.circle(frame, (x_pos, y_pos), 5, (0, 0, 255), -1)
            # otherwise, colour it green
            else:
                cv2.circle(frame, (x_pos, y_pos), 5, (0, 255, 0), -1)
            
            # draw a black outline around the vertex
            cv2.circle(frame, (x_pos, y_pos), 5, (0, 0, 0), 2)
            
            # if the current vertex us too close to the edge of the screen (such
            #   that the text falls off), move it so that the text is visible
            if x_pos >= (frame.shape[1] - (frame.shape[1] * 0.92)):
                text_x = x_pos - 75
            if y_pos <= (frame.shape[0] * 0.02):
                text_y = y_pos + 15
            
            # draw coordinate text
            cv2.putText(frame, '{}, {}'.format(x_pos, y_pos), (text_x, text_y),
                        fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale = 0.45,
                        color = (0, 255, 0), thickness = 1)
    ###
    
    def move_roi_vertex(self, mouse_x, mouse_y):
        """ Check if the mouse if currently over a ROI vertex,
            and move it if it is active (clicked)
        """
        threshold = 5 # how far (pixels) from the center of a vertex counts as 'over' it
        
        # check if the mouse is currently over a ROI vertex
        for i, (vert_x, vert_y) in enumerate(self.roi_vertices):
            # if the vertex is within the x threshold
            if mouse_x > (vert_x - threshold) and mouse_x < (vert_x + threshold):
                # if the vertex is within the y threshold
                if mouse_y > (vert_y - threshold) and mouse_y < (vert_y + threshold):
                    self.selected_vtx_id = i
                    break
                    
            # if the mouse isn't over any of the vertices, mark as such (-1)
            self.selected_vtx_id = -1
        
        # move active vertex to current mouse position
        if self.active_vtx_id != -1:
            self.roi_vertices[self.active_vtx_id][0] = mouse_x
            self.roi_vertices[self.active_vtx_id][1] = mouse_y
    ###
    
    def update(self, frame):
        """ Update the pre-processor object, and print adjustments to the frame(s) """
        # ensure that each ROI vertex lie within the boundaries of the frame. If not,
        #   move it to the edge of the 
        for i, (vtx_x, vtx_y) in enumerate(self.roi_vertices):
            if vtx_x < 0:
                self.roi_vertices[i][0] = 0
            if vtx_y < 0:
                self.roi_vertices[i][1] = 0
            if vtx_x > (frame.shape[1] - 1):
                self.roi_vertices[i][0] = frame.shape[1]
            if vtx_y > (frame.shape[0] - 1):
                self.roi_vertices[i][1] = frame.shape[0]
        
        # draw the ROI to the original frame
        self.draw_roi(frame)
    ###
    
    def process_frame(self, frame):
        """ Apply various pre-processing techniques to a frame """
        processed_frame = frame.copy() # copy the frame for processing
        
        # apply a four-point perspective transform if there are 4 vertices
        if len(self.roi_vertices) == 4:
            processed_frame, _ = four_point_transform(frame, self.roi_vertices)
        
        # apply HSL saturation thresholding to identify yellow lane markings
        sat_binary = colour_thresholding(processed_frame, self.sat_threshold,
                                           self.val_threshold).astype(np.uint8)
        
        return processed_frame
    ###

def four_point_transform(frame, vertices):
    """ Apply a four-point perspective transform to a frame, using a region of interest """
    frame_shape = frame.shape # store frame dimensions
    
    # define source and destination vertices
    src = np.float32(vertices)
    dst = np.float32([[0, frame.shape[0]], [0,0],
                     [frame.shape[1], 0], [frame.shape[1], frame.shape[0]]])
    
    # create transformation matrices
    transform_matrix = cv2.getPerspectiveTransform(src, dst)
    inv_transform_matrix = cv2.getPerspectiveTransform(dst, src) # inverted
    
    # perform perspective warp
    frame_size = (frame_shape[1], frame_shape[0])
    warped_frame = cv2.warpPerspective(frame, transform_matrix, frame_size,
                                       flags=cv2.INTER_LINEAR)
    
    # transform frame back to original perspective
    # warped_frame = cv2.warpPerspective(warped_frame, inv_transform_matrix,
    #                                    frame_size, flags=cv2.INTER_LINEAR)
    
    return warped_frame, inv_transform_matrix
###

def colour_thresholding(frame, sat_threshold, val_threshold):
    """ ... """
    # convert the frame to HLS and HSV colour spaces
    hls_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2HLS).astype(np.float)
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV).astype(np.float)
    
    # extract saturation and value channels
    sat_channel = hls_frame[:,:,2].astype(np.uint8)
    val_channel = hsv_frame[:,:,2].astype(np.uint8)
    
    # create saturation and value binaries
    sat_binary = np.zeros_like(sat_channel).astype(np.uint8)
    sat_binary[(sat_channel > sat_threshold[0]) & (sat_channel <= sat_threshold[1])] = 1
    
    val_binary = np.zeros_like(val_channel).astype(np.uint8)
    val_binary[(val_channel > val_threshold[0]) & (val_channel <= val_threshold[1])] = 1
    
    # combine the binaries
    combined_binary = ((sat_binary == 1) | (val_binary == 1))
    
    # plot binaries
    # plt.imshow(sat_binary * 255, cmap='gray')
    # plt.imshow(val_binary * 255, cmap='gray')
    plt.imshow(combined_binary * 255, cmap='gray')
    
    return combined_binary
###