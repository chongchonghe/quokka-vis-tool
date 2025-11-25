import matplotlib.pyplot as plt
import matplotlib.patches as patches

def add_scalebar(ax, length, label, h=0.014, left=0.03, right=None,
                 color='w', gap=0.01, **kwargs):
    """ Add a scalebar to a figure
    Author: ChongChong He

    Parameters
    ----------
    ax: matplotlib axes
        The axes passed to add_scalebar
    length: double
        The length of the scalebar in code units
    label: string
        The scalebar label
    h: double
        The height of the scalebar relative to figure height
    color: string
        color
    **kwargs: dict
        kwargs passed to ax.text

    Examples
    --------
    >>> im = plt.imread("/Users/chongchonghe/Pictures/bj.jpg")[:800, :800, :]
    >>> plt.imshow(im)
    >>> ax = plt.gca()
    >>> add_scalebar(ax, 200, '3 pc')
    >>> plt.show()

    """
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    if right is None:
        left_pos = xlim[0] + left * (xlim[1] - xlim[0])
    else:
        left_pos = xlim[0] + right * (xlim[1] - xlim[0]) - length
    bottom = 0.03
    bottom_pos = ylim[0] + bottom * (ylim[1] - ylim[0])
    rect = patches.Rectangle((left_pos, bottom_pos), length, h*(ylim[1] - ylim[0]),
                     facecolor=color, edgecolor=None)

    ax.add_patch(rect)
    ax.text(
        left_pos + 0.5*length,
        ylim[0] + (h + bottom + gap) * (ylim[1] - ylim[0]),
        label,
        ha='center', va='bottom',
        color=color,
        **kwargs,
    )

def to_boxlen(quant, ds):
    if type(quant) == tuple:
        return float(yt.YTQuantity(*quant) / ds.length_unit)
    else:
        return quant

def annotate_scale_bar(scale):
    if scale is not None:
        coeff, unit = scale
        leng = to_boxlen((coeff, unit), ds)
        label = f"{coeff} {unit}"
        if scaleloc == "lower_left":
            left, right = 0.06, None
        else:
            left, right = None, 0.94
        add_scalebar(
            ax, leng, label=label, left=left, right=right, 
            fontsize="large")