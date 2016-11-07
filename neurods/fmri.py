"""Utilities for fMRI section of CogNeuro Connector for Data8"""

import numpy as np
import nibabel
import scipy.stats
import warnings
import numpy as np


### Created for HW for week 7
def load_data(fname, mask=None, standardize=False):
    """Load fMRI data from nifti file, optionally with masking and standardization"""
    if isinstance(fname, (list, tuple)):
        return np.vstack([load_data(f, mask=mask, standardize=standardize) for f in fname])
    nii = nibabel.load(fname)
    data = nii.get_data().T.astype(np.float32)
    if mask is not None:
        data = data[:, mask]
    if standardize:
        data = scipy.stats.zscore(data, axis=0)
    return data

### Created for HW for week 8
def unmask(data, mask, bg_value=0):
    """Unmask 1D or 2D data (put back into 3D brain shape)

    Parameters
    ----------
    data : array (1D or 2D)
        Data to be unmasked. Must be 1D or 2D, not more.
    mask : array (bool)
        Boolean mask that was used to mask data.
    bg_value : scalar
        Value to be inserted into masked-out parts of 3D volume.
    """
    if np.ndim(data)==1:
        br = np.ones(mask.shape) * bg_value
        br[mask] = data
    elif np.ndim(data)==2:
        br = np.ones((data.shape[0],)+mask.shape) * bg_value
        br[:, mask] = data
    else:
        raise Exception("Can't unmask > 2D data!")
    return br


### Created for HW for week 8
def compute_event_avg(data, events, time_per_event):
    """Columns of `events` are markers for different types of events
    events are event onsets OR 
    data should be columns
    """
    # 1D data for now
    if events.dtype in (np.bool, ):
        event_start = np.nonzero(events)[0]
    else:
        event_start = events
    event_stack = []
    for st, fin in zip(event_start, event_start+time_per_event):
        tmp = data[st:fin]
        if fin > len(data):
            tmp = np.hstack([tmp, np.zeros(fin-len(data))])
        event_stack.append(tmp)
    event_stack = np.nanmean(event_stack, axis=0)
    return event_stack


def hrf(shape='twogamma', tr=1, pttp=5, nttp=15, pos_neg_ratio=6, onset=0, pdsp=1, ndsp=1, t=None):
    """Create canonical hemodynamic response filter
    
    Parameters
    ----------
    shape : string, {'twogamma'|'boynton'}
        HRF general shape {'twogamma' [, 'boynton']}
    tr : scalar
        HRF sample frequency, in seconds (default = 2)
    pttp : scalar
        time to positive (response) peak in seconds (default = 5)
    nttp : scalar
        Time to negative (undershoot) peak in seconds (default = 15)
    pos_neg_ratio : scalar
        Positive-to-negative ratio (default: 6, OK: [1 .. Inf])
    onset : 
        Onset of the HRF (default: 0 secs, OK: [-5 .. 5])
    pdsp : 
        Dispersion of positive gamma PDF (default: 1)
    ndsp : 
        Dispersion of negative gamma PDF (default: 1)
    t : vector | None
        Sampling range (default: [0, onset + 2 * (nttp + 1)])
    
    Returns
    -------
    h : HRF function given within [0 .. onset + 2*nttp]
    t : HRF sample points
    
    Notes
    -----
    The pttp and nttp parameters are increased by 1 before given
    as parameters into the scipy.stats.gamma.pdf function (which is a property
    of the gamma PDF!)

    Based on hrf function in matlab toolbox `BVQXtools`; converted to python and simplified by ML 
    Version:  v0.7f
    Build:    8110521
    Date:     Nov-05 2008, 9:00 PM CET
    Author:   Jochen Weber, SCAN Unit, Columbia University, NYC, NY, USA
    URL/Info: http://wiki.brainvoyager.com/BVQXtools
    """

    # Input checks
    if not shape.lower() in ('twogamma', 'boynton'):
        warnings.warn('Shape can only be "twogamma" or "boynton"')
        shape = 'twogamma'
    if t is None:
        t = np.arange(0, (onset + 2 * (nttp + 1)), tr) - onset
    else:
        t = np.arange(np.min(t), np.max(t), tr) - onset;

    # Create filter
    h = np.zeros((len(t), ))
    if shape.lower()=='boynton':
        # boynton (single-gamma) HRF
        h = scipy.stats.gamma.pdf(t, pttp + 1, pdsp)
    elif shape.lower()=='twogamma':
        gpos = scipy.stats.gamma.pdf(t, pttp + 1, pdsp)
        gneg = scipy.stats.gamma.pdf(t, nttp + 1, ndsp) / pos_neg_ratio
        h =  gpos-gneg 
    h /= np.sum(h)
    return t, h


def simple_convolution(data, kernel):
    """Simple 1-D convolution function
    
    See also: https://en.wikipedia.org/wiki/Convolution
    """
    nk = len(kernel)
    nd = len(data)
    # Pad data with zeros
    data_ = np.pad(data, (nk-1, nk), 'constant', constant_values=0)
    # Preallocate output
    out = np.zeros((nd+nk*2, ))
    # Loop through data
    for i in range(len(data_)):
        if i+nk > len(data_):
            # Stop once we run out of data
            break
        out[i] = np.sum(data_[i:(i+nk)] * kernel[::-1]) # (note reversal of convolution kernel)
    # clip output to length of original data
    out = out[:nd] 
    return out

def apply_hrf(X, tr=2, **kwargs):
    """Apply hrf to design matrix"""
    t, hrf_ = hrf(tr=tr, **kwargs)
    Xh = np.array([np.convolve(x, hrf_, mode='full')[:len(x)] for x in X.T]).T
    return Xh

