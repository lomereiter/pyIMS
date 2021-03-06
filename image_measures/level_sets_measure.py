''' Function for calculating a measure of image noise using level sets
# Inputs: image - numpy array of pixel intensities
         nlevels - number of levels to calculate over (note that we approximating a continuious distribution with a 'large enough' number of levels)
# Outputs: measure_value
 
This function calculates the number of connected regions above a threshold at an evenly spaced number of threshold
between the min and max values of the image.

There is some morphological operations to deal with orphaned pixels and heuristic parameters in the image processing.

# Usage    
img = misc.imread('/Users/palmer/Copy/ion_image.png').astype(float)
print measure_of_chaos(img,20)
 '''

# try to use cv2 for faster image processing
try:
    import cv2
    cv2.connectedComponents # relatively recent addition, so check presence
    opencv_found = True
except (ImportError, AttributeError):
    opencv_found = False

def measure_of_chaos(im,nlevels,interp='interpolate',q_val = 99.): 
    global opencv_found
    import numpy as np
    from scipy import ndimage, misc, ndarray, interpolate 
    from scipy.signal import medfilt
    
    def clean_image(im_clean,interp):
        # Image properties
        notnull=im_clean>0 #does not include nan values
        im_clean[notnull==False]=0
        im_size=np.shape(im_clean)
        # hot spot removal (quantile threshold)
        im_q = np.percentile(im_clean[notnull],q_val)
        im_rep =  im_clean>im_q       
        im_clean[im_rep] = im_q 
        # interpolate to clean missing values   
        if interp == '' or interp==False:
            #do nothing
            im_clean=im_clean        
        elif interp == 'interpolate' or interp==True:        # interpolate to replace missing data - not always present
            try:
                # interpolate to replace missing data - not always present
                X,Y=np.meshgrid(np.arange(0,im_size[1]),np.arange(0,im_size[0]))
                f=interpolate.interp2d(X[notnull],Y[notnull],im_clean[notnull])
                im_clean=f(np.arange(0,im_size[1]),np.arange(0,im_size[0]))
            except:
                print 'interp bail out'                
                clean = np.zeros(np.shape(im)) # if interp fails, bail out
        elif interp=='median':
                im_clean = medfilt(im_clean)
        else:
            raise ValueError('{}: interp option not recognised'.format(interp))
        # scale max to 1
        im_clean = im_clean/im_q 
        return im_clean

    ## Image Pre-Processing
    # don't process empty images
    if np.sum(im)==0:
        return np.nan,[],[],[]
    sum_notnull = np.sum(im > 0)
    #reject very sparse images
    if sum_notnull < 4:
        return np.nan,[],[],[]
    im=clean_image(im,interp)

    ## Level Sets Calculation
    # calculate levels
    levels = np.linspace(0,1,nlevels) #np.amin(im), np.amax(im)
    # hardcoded morphology masks
    dilate_mask = np.array([[0,1,0],[1,1,1],[0,1,0]], dtype=np.uint8)
    erode_mask = np.array([[1,1,1],[1,1,1],[1,1,1]], dtype=np.uint8)
    label_mask = np.ones((3,3))

    def count_objects_ndimage(im, lev):
        # Threshold at level
        bw = (im > lev)
        # Morphological operations
        bw=ndimage.morphology.binary_dilation(bw,structure=dilate_mask)
        bw=ndimage.morphology.binary_erosion(bw,structure=erode_mask)
        # Record objects at this level
        return ndimage.label(bw)[1] #second output is number of objects

    def count_objects_opencv(im, lev):
        bw = (im > lev).astype(np.uint8)
        cv2.dilate(bw, dilate_mask)
        cv2.erode(bw, erode_mask)
        return cv2.connectedComponents(bw)[0] - 1 # extra obj is background

    count_objects = count_objects_opencv if opencv_found else count_objects_ndimage

    # Go through levels and calculate number of objects
    num_objs = [count_objects(im, level) for level in levels]
    measure_value = float(np.sum(num_objs))/(sum_notnull*nlevels)
    return measure_value,im,levels,num_objs


