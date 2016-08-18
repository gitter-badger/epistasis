import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from scipy.stats import norm as scipy_norm
from seqspace.errors import upper_transform, lower_transform
from epistasis.utils import Bunch

def epistasis(betas=[], labels=[], errors=None, **kwargs):
    """
    Create a barplot with the values from model, drawing the x-axis as a grid of
    boxes indicating the coordinate of the epistatic parameter. Should automatically
    generate an almost publication-quality figure.

    Parameters
    ----------
    betas : array
        an array of epistatic coefficients
    labels : array
        array of epistatic indices/labels.
    errors : 2d array or list
        upper and lower bounds for each beta.

    Keyword arguments
    -----------------
    logbase : numpy.ufunc (default=np.log10)
        function to transform into log space
    log_transform : bool (default=False)
        transform the betas if true.
    order_colors :
        list/tuple of colors for each order (rgb,html string-like)
    significance :
        how to treat signifiance.  should be
        1. "bon" -> Bonferroni corrected p-values (default)
        2. "p" -> raw p-values
        3. None -> ignore significance
    significance_cutoff :
        value above which to consider a term significant
    sigmas :
        number of sigmas to show for each error bar
    y_scalar :
        how much to scale the y-axis above and beyond y-max
    y_axis_name :
        what to put on the y-axis of the barplot
    figsize :
        tuple of figure width,height
    height_ratio :
        how much to scale barplot relative to xbox
    star_cutoffs :
        signifiance cutoffs for star stack.  should go from highest
                  p to lowest p (least to most significant)
    star_spacer :
        constant that scales how closely stacked stars are from one
        another
    ybounds : tuple (default=None)
    bar_borders : bool (default=True)
    xgrid : bool (default=True)
    ecolor : color (default='black')
    elinewidth : float (default=1)
    capthick : float (default=1)
    capsize : float (default=1)

    Returns
    -------
        pretty-graph objects fig and ax_array (ax_array has two entries for top
        and bottom panels)
    """
    ## Set up plotting user options. Type check the options to make sure nothing
    # will break. Also helps with widgets.

    defaults = {
        "order_colors" : ("red","orange","green","purple","DeepSkyBlue","yellow","pink"),
        "logbase" : np.log10,
        "log_transform" : False,
        "significance" : "bon",
        "significance_cutoff" : 0.05,
        "sigmas" : 0,
        "log_space" : False,
        "y_scalar" : 1.5,
        "y_axis_name" : "interaction",
        "figwidth" : 5,
        "figheight": 3,
        "figsize" : (5,3),
        "height_ratio" : 12,
        "star_cutoffs" : (0.05,0.01,0.001),
        "star_spacer" : 0.0075,
        "ybounds"  : None,
        "bar_borders" : True,
        "xgrid" : True,
        "ecolor" : "black",
        "capthick" : 1,
        "capsize" : 1,
        "elinewidth" : 1,
        "save" : False,
        "fname" : "figure.svg",
        "format" : "svg",
    }
    #types = dict([(key, type(val)) for key, val in defaults.items()])
    #defaults.update(kwargs)
    #options = objectify(defaults)
    options = Bunch(**defaults)
    options.update(**kwargs)
    # Construct keyword arguments
    error_kw = {
        "ecolor" : options.ecolor,
        "capsize" : options.capsize,
        "elinewidth" : options.elinewidth,
        "capthick" : options.capthick,
    }
    if "figsize" in kwargs:
        options.figsize = kwargs["figsize"]
    else:
        options.figsize = (options.figwidth, options.figheight)

    # Name all variables that matter for this function
    if labels[0] == [0]:
        labels = labels[1:]
        betas = betas[1:]
        if errors is not None:
            upper = errors[1][1:]
            lower = errors[0][1:]
    else:
        if errors is not None:
            upper = errors[1]
            lower = errors[0]

    # Sanity check on the errors
    if options.sigmas == 0:
        significance = None
    elif options.significance == None:
        sigmas = 0

    # Figure out the length of the x-axis and the highest epistasis observed
    num_terms = len(labels)
    highest_order = max([len(l) for l in labels])

    # Figure out how many sites are in the dataset (in case of non-binary system)
    all_sites = []
    for l in labels:
        all_sites.extend(l)
    all_sites = list(dict([(s,[]) for s in all_sites]).keys())
    all_sites.sort()
    num_sites = len(all_sites)

    # Figure out how to color each order
    if options.order_colors == None:
        options.order_colors = ["gray" for i in range(highest_order+1)]
    else:
        if len(options.order_colors) < highest_order:
            err = "order_colors has too few entries (at least {:d} needed)\n".format(highest_order)
            raise ValueError(err)

        # Stick gray in the 0 position for insignificant values
        options.order_colors = list(options.order_colors)
        options.order_colors.insert(0,"gray")

    # ---------------------- #
    # Deal with significance #
    # ---------------------- #
    # NEED TO RETURN TO SIGNIFICANCE FUNCTIONS
    if options.sigmas == 0:
        options.significance = None
    else:
        # If log transformed, need to get raw values for normal distribution
        if options.log_transform:
            z_score =  abs( (betas  - 1 )/upper )
        # else, just grab standard values
        else:
            z_score =  abs( (betas)/upper )

        # if z_score is > 5, set z_score to largest possible range where p-value is within floating point
        z_score[z_score > 8.2] = 8.2

    # straight p-values
    if options.significance == "p":
        p_values = 2*(1 - scipy_norm.cdf( z_score ) )

    # bonferroni corrected p-values
    elif options.significance == "bon":
        p_values = 2*(1 - scipy_norm.cdf( z_score ) ) * len(betas)

    # ignore p-values and color everything
    elif options.significance == None:
        p_values = [0 for i in range(len(labels))]
        options.significance_cutoff = 1.0

    # or die
    else:
        err = "signifiance argument {:s} not recognized\n".format(options.significance)
        raise ValueError(err)

    # Create color array based on significance
    color_array = np.zeros((len(labels)),dtype=int)
    for i, l in enumerate(labels):
        if p_values[i] < options.significance_cutoff:
            color_array[i] = len(l) - 1
        else:
            color_array[i] = -1

    # ---------------- #
    # Create the plots #
    # ---------------- #

    # Make a color map
    cmap = mpl.colors.ListedColormap(colors=options.order_colors)
    cmap.set_bad(color='w', alpha=0) # set the 'bad' values (nan) to be white and transparent
    bounds = range(-1,len(options.order_colors))
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

    if options.xgrid is True:
        fig = plt.figure(figsize=options.figsize)

        # Create a plot with an upper and lower panel, sharing the x-axis
        gs = mpl.gridspec.GridSpec(2, 1, height_ratios=[options.height_ratio, 1])
        ax = [plt.subplot(gs[0])]
        ax.append(plt.subplot(gs[1],sharex=ax[0]))
        bar_axis = ax[0]
        grid_axis = ax[1]
        ###### Create the box-array x-axis

        # make an empty data set
        data = np.ones((num_sites,num_terms),dtype=int)*np.nan

        # Make entries corresponding to each coordinate 1
        for i, l in enumerate(labels):
            for j in l:
                data[(j-1),i] = color_array[i]
        # draw the grid
        for i in range(num_terms + 1):
            grid_axis.add_artist(mpl.lines.Line2D((i,i),
               (0,num_sites),
               color="black"))
        for i in range(num_sites + 1):
            grid_axis.add_artist(mpl.lines.Line2D((0,num_terms),
               (i,i),
               color="black"))
        # draw the boxes
        grid_axis.imshow(data, interpolation='nearest',cmap=cmap,norm=norm,
                           extent=[0, num_terms, 0, num_sites], zorder=0)

        # turn off the axis labels
        grid_axis.set_frame_on(False)
        grid_axis.axis("off")
        grid_axis.set_xticklabels([])
        grid_axis.set_yticklabels([])

    else:

        fig, ax = plt.subplots(figsize=options.figsize)
        bar_axis = ax


    # ------------------ #
    # Create the barplot #
    # ------------------ #

    # set up bar colors
    colors_for_bar = np.array([mpl.colors.colorConverter.to_rgba(options.order_colors[(i+1)]) for i in color_array])

    # Plot without errors
    if options.sigmas == 0:
        if log_space:
            bar_y = options.logbase(betas)
        else:
            bar_y = betas
        bar_axis.bar(range(len(bar_y)), bar_y, width=0.8, color=colors_for_bar, edgecolor="none")
    # plot with errors
    else:
        bar_y = betas
        upper = options.sigmas*upper
        lower = options.sigmas*lower       # Plot the graph on a log scale
        if options.log_space:
            new_bar_y = options.logbase(bar_y)
            new_upper = upper_transform(bar_y, upper, options.logbase)
            new_lower = lower_transform(bar_y, lower, options.logbase)
        # else if the space is log transformed, plot the non-log interaction values
        else:
            new_upper = upper
            new_lower = lower
            new_bar_y = bar_y
        yerr = [new_lower, new_upper]
        # Plot
        bar_axis.bar(range(len(new_bar_y)), new_bar_y,
            width=0.8,
            yerr=yerr,
            color=colors_for_bar,
            error_kw=error_kw,
            edgecolor="none",
            linewidth=2)
    # Add horizontal lines for each order
    bar_axis.hlines(0, 0, len(betas)-1, linewidth=1, linestyle="-", zorder=0)
    # Label barplot y-axis
    bar_axis.set_ylabel(options.y_axis_name, fontsize=14)
    # Set barplot y-scale
    if options.ybounds is None:
        ymin = -options.y_scalar*max(abs(bar_y))
        ymax =  options.y_scalar*max(abs(bar_y))
    else:
        ymin = options.ybounds[0]
        ymax = options.ybounds[1]

    # Make axes pretty pretty
    bar_axis.axis([-1, len(bar_y) + 1, ymin, ymax])
    bar_axis.set_frame_on(False) #axis("off")
    bar_axis.get_xaxis().set_visible(False)
    bar_axis.get_yaxis().tick_left()
    bar_axis.get_yaxis().set_tick_params(direction='out')
    bar_axis.add_artist(mpl.lines.Line2D((-1,-1), (bar_axis.get_yticks()[1], bar_axis.get_yticks()[-2]), color='black', linewidth=1))

    # add vertical lines between order breaks
    previous_order = 1
    for i in range(len(labels)):
        if len(labels[i]) != previous_order:
            bar_axis.add_artist(mpl.lines.Line2D((i,i),
               (ymin,ymax),
               color="black",
               linestyle=":",
               linewidth=1))
            previous_order = len(labels[i])

    # ------------------------- #
    # Create significance stars #
    # ------------------------- #
    if options.sigmas != 0:
        min_offset = options.star_spacer*(ymax-ymin)
        for i in range(len(p_values)):

            star_counter = 0
            for j in range(len(options.star_cutoffs)):
                if p_values[i] < options.star_cutoffs[j]:
                    star_counter += 1
                else:
                    break

            for j in range(star_counter):
                bar_axis.text(x=(i+0),y=ymin+(j*min_offset),s="*", fontsize=16)

    # remove x tick labels
    try:
        plt.setp([a.get_xticklabels() for a in fig.axes[:-1]], visible=False)
    except IndexError:
        pass

    # Draw the final figure
    fig.tight_layout()

    if options.save:
        fig.savefig(options.fname, format=options.format)

    return fig, ax
