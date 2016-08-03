"""Functions for data visualization"""
import matplotlib.pyplot as plt
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import itertools
import mne


def find_squarish_dimensions(n):
    """Get balanced (approximately square) numbers of rows & columns for n elements

    Returns (nearly) sqrt dimensions for a given number. e.g. for 23, will
    return [5, 5] and for 26 it will return [6, 5]. Useful for creating displays of
    sets of images. Always sets x greater than y if x != y

    Returns
    -------
    x : int
       larger dimension (if not equal)
    y : int
       smaller dimension (if not equal)
    """
    sq = np.sqrt(n)
    if round(sq)==sq:
        # If n is a perfect square
        x, y = sq, sq
    else:
        # Take either bigger square (first entries) or asymmetrical square (second entries)
        x_poss = [np.ceil(sq), np.ceil(sq)]
        y_poss = [np.ceil(sq), np.floor(sq)]
        n_elements = [x*y for x, y in zip(x_poss, y_poss)]
        err = np.array([n_e-n for n_e in n_elements])
        # Make sure negative values will not be chosen as the minimum
        err[err<0] = 1000 
        best_idx = np.argmin(err)
        x = x_poss[best_idx]
        y = y_poss[best_idx]
    return x, y


### --- Created in week 8 --- ###

def slice_3d_array(volume, axis=2, fig=None, vmin=None, vmax=None, cmap=plt.cm.gray, nr=None, nc=None ):
    """Slices 3D array along arbitrary axis

    Parameters
    ----------
    volume : np.array (3D)
        Data to be shown
    axis : int | 0, 1, [2] (optional)
       axis along which to divide the array into slices
    fig : plt.figure
        figure in which to plot array slices

    Other Parameters
    ----------------
    vmin : float [max(volume)] (optional) 
       color axis minimum
    vmax : float [min(volume)] (optional)
       color axis maximum
    cmap : matplotlib colormap instance [plt.cm.gray] (optional)
        color map for data
    nr : int (optional)
       number of rows
    nc : int (optional)
       number of columns
    """
    if fig is None:
        fig = plt.figure()
    if nr is None or nc is None:
        nc, nr = find_squarish_dimensions(volume.shape[axis])
    if vmin is None:
        vmin = np.nanmin(volume)
    if vmax is None:
        vmax = np.nanmax(volume)
    l_edges = np.linspace(0, 1, nc+1)[:-1]
    b_edges = np.linspace(1, 0, nr+1)[1:]
    width = 1/float(nc)
    height = 1/float(nr)
    bottoms, lefts = zip(*list(itertools.product(b_edges, l_edges)))
    for ni, sl in enumerate(np.split(volume, volume.shape[axis], axis=axis)):
        ax = fig.add_axes((lefts[ni], bottoms[ni], width, height))
        ax.imshow(sl.squeeze(), vmin=vmin, vmax=vmax, interpolation="nearest", cmap=cmap)
        ax.set_xticks([])
        ax.set_yticks([])
    return fig

### --- Created in week 9 --- ###
def show_design_matrix(X, conditions=None, time_unit='s'):
    """Simple display of design matrix for an experiment, as an image"""
    n_trs, n_channels = X.shape
    plt.imshow(X.T)
    plt.xlabel('Time ({})'.format(time_unit))
    plt.ylabel('Condition')
    if conditions is None:
        conditions = np.arange(1, n_channels+1)
    plt.yticks(range(n_channels), conditions)


def plot_activity_on_brain(x, y, act, im, smin=10, smax=100, vmin=None,
                           vmax=None, ax=None, cmap=None, name=None):
    """Plot activity as a scatterplot on a brain.

    Parameters
    ----------
    x : array, shape (n_channels,)
        The x positions of electrodes
    y : array, shape (n_channels, )
        The y positions of electrodes
    act : array, shape (n_channels,)
        The activity values to plot as size/color on electrodes
    im : ndarray, passed to imshow
        An image of the brain to match with x/y positions
    smin : int
        The minimum size of points
    smax : int
        The maximum size of points
    vmin : float | None
        The minimum color value / size cutoff
    vmax : float | None
        The maximum color value / size cutoff
    ax : axis | None
        An axis object to plot to
    cmap : matplotlib colormap | None
        The colormap to plot
    name : string | None
        A string name for the plot title.

    Returns
    -------
    ax : axis
        The axis object for the plot
    """
    # Handle defaults
    if ax is None:
        _, ax = plt.subplots()
    if cmap is None:
        cmap = plt.cm.coolwarm
    vmin = act.min() if vmin is None else vmin
    vmax = act.max() if vmax is None else vmax

    # Define colors + sizes
    act_norm = (act - vmin) / float(vmax - vmin)
    colors = cmap(act_norm)
    sizes = np.clip(np.abs(act) / float(vmax), 0, 1)  # Normalize bw 0 and 1
    sizes = MinMaxScaler((smin, smax)).fit_transform(sizes[:, np.newaxis])

    # Plotting
    ax.imshow(im)
    ax.scatter(x, y, s=sizes, c=colors, cmap=cmap)
    ax.set_title(name, fontsize=20)
    return ax


def xy_to_layout(xy, image, ch_names=None, flipy=True):
    """Convert xy coordinates to an MNE layout, normalized by an image

    Parameters
    ----------
    xy : array, shape (n_points, 2)
        xy coordinates of electrodes
    image : ndarray
        The image of the brain that xy positions plot on top of
    ch_names : None | list of strings, length n_points
        Channel names for each xy point
    flipy : bool
        Whether or not to flip the y coordinates of xy points after
        creating the layout (use if xy points are from the bottom-up,
        because imshow will plot from the top-down)

    Returns
    -------
    lt : instance of MNE layout
        The layout of these xy positions
    """
    if ch_names is None:
        ch_names = ['%s' % ii for ii in range(xy.shape[0])]
    lt = mne.channels.generate_2d_layout(xy, bg_image=image,
                                         ch_names=ch_names)

    if flipy is True:
        # Flip the y-values so they plot from top to bottom
        lt.pos[:, 1] = 1 - lt.pos[:, 1]
    return lt


def plot_tfr(times, freqs, tfr, ax=None, use_log=True,
             baseline=None, linear_y=True):
    """Plot a time-frequency representation."""
    if ax is None:
        f, ax = plt.subplots()
    if use_log is True:
        tfr = np.log(tfr)
    if baseline is not None:
        tfr = mne.baseline.rescale(tfr, times, baseline, mode='zscore')
        vmin, vmax = (-6, 6)
    else:
        vmin, vmax = (None, None)
    if linear_y is True:
        freqs = np.arange(freqs.shape[0])
    ax.pcolormesh(times, freqs, tfr, cmap=plt.cm.coolwarm, vmin=vmin, vmax=vmax)
    ax.set_xlim([times.min(), times.max()])
    ax.set_ylim([freqs.min(), freqs.max()])
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Frequency (Hz)')
    return ax