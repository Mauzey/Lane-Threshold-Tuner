# -*- coding: utf-8 -*-
# import modules
import numpy as np
import cv2

class PreProcessor():
    def __init__(self):
        self.roi_vertices = [] # vertices which define a region of interest
        self.selected_vtx_id = -1 # stores id of the vertex the mouse is over (-1 = None)
        self.active_vtx_id = -1 # stores the id of the active vertex
        
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
        """ ... """
        # check if the mouse is currently over a ROI vertex
        # -------------------------------------------------
        threshold = 5 # how far (pixels) from the center of a vertex counts as 'over' it
        
        for i, (vert_x, vert_y) in enumerate(self.roi_vertices):
            # if the vertex is within the x threshold
            if mouse_x > (vert_x - threshold) and mouse_x < (vert_x + threshold):
                # if the vertex is within the y threshold
                if mouse_y > (vert_y - threshold) and mouse_y < (vert_y + threshold):
                    self.selected_vtx_id = i
                    break
                    
            # if the mouse isn't over any of the vertices, mark as such (-1)
            self.selected_vtx_id = -1
        # -------------------------------------------------
        
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
            processed_frame = four_point_transform(frame, self.roi_vertices)
        
        return processed_frame
    ###

def four_point_transform(frame, vtcs):
    """ Apply a four-point transform to a frame using a region of interest """
    # sort ROI vertices into the following order:
    #   top-left -> top-right -> bottom-right -> bottom-left
    # ----------------------------------------------------
    vertices = [] # stores the ROI vertices
    ordered_vertices = np.zeros((4, 2), dtype='float32') # stores ordered vertices
    
    print(vtcs)
    
    for i, vertex in enumerate(vtcs):
        print(i)
        vertices.append((vertex[0], vertex[1]))
    
    vertices = np.array(eval(vertices, dtype='float32'))
    
    print(vertices)
    
    # the top-left point will have the smallest sum (x_pos + y_pos). Similarly,
    #   the bottom-right point will have the greatest
    vertices_sum = vertices.sum(axis=1)
    ordered_vertices[0] = vertices[np.argmin(vertices_sum)]
    ordered_vertices[2] = vertices[np.argmax(vertices_sum)]
    
    # the top-right vertex will have the largest difference in x_pos and y_pos
    #   values. Similarly, the bottom-left will have the largest
    vertices_diff = np.diff(vertices, axis=1)
    ordered_vertices[1] = vertices[np.argmin(vertices_diff)]
    ordered_vertices[3] = vertices[np.argmax(vertices_diff)]
    # ----------------------------------------------------
    
    # split the ordered vertices
    top_l, top_r, btm_r, btm_l = ordered_vertices
    
    # perform the four-point transform on the ROI and return as a warped frame
    # ------------------------------------------------------------------------
    
    # determine the width of the transformed frame, which will be either the
    #   maximum distance between the top-left and top-right x_pos or the
    #   bottom-left and bottom-right x_pos
    top_width = np.sqrt(((top_r[0] - top_l[0]) ** 2) + ((top_r[1] - top_l[1]) ** 2))
    btm_width = np.sqrt(((btm_r[0] - btm_l[0]) ** 2) + ((btm_r[1] - btm_l[1]) ** 2))
    max_width = max(int(top_width), int(btm_width))
    
    # determine the height of the transformed frame, which will be either the
    #   maximum distance between the top-left and bottom-left y_pos or the
    #   top-right and bottom-right y_pos
    left_height = np.sqrt(((top_l[0] - btm_l[0]) ** 2) + ((top_l[1] - btm_l[1]) ** 2))
    right_height = np.sqrt(((top_r[0] - btm_r[0]) ** 2) + ((top_r[1] - btm_r[1]) ** 2))
    max_height = max(int(left_height), int(right_height))
    
    # define a set of destination vertices for the new frame in order to obtain
    #   a 'top-down' view. These vertices are in the same order as the original
    #   vertices: 
    #       top-left -> top-right -> bottom-right -> bottom-left
    destination_vertices = np.array([
                            [0, 0],
                            [max_width - 1, 0],
                            [max_width - 1, max_height - 1],
                            [0, max_height - 1]], dtype='float32')
    
    # compute and apply the perspective transform matrix
    transform_matrix = cv2.getPerspectiveTransform(ordered_vertices, destination_vertices)
    warped_frame = cv2.warpPerspective(frame, transform_matrix, (max_width, max_height))
    
    return warped_frame
###