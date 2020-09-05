# Lane Detection Threshold Tuner (WIP)
## Functionality
* User can dynamically define a region of interest (ROI)
  - A four-point perspective transform is then applied to the frame based on this ROI
* Users can enable/disable and adjust the parameters of the following:
  - HLS Saturation Thresholding, in order to identify yellow lane markings
  - Histogram Equilized Thresholding, in order to identify white lane markings
