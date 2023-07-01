"""
This module contains functions useful for exploring data parsed from the
English Catalogues
"""

import pandas as pd


def histogram_strings_by_length(
        path,
        bins=range(0, 400, 5),
        underflow_lim=30,
        overflow_lim=300,
        show_over_under=False,
        drop_nulls=False,
        title='Lengths of entries',
        xlabel='Number of characters in an entry',
        ylabel='Number of entries found'
):
    '''
    Plot a histogram the lengths of strings in the first column of a csv
    file at the path provided.

    Parameters
    ----------
    path : str
        The path to the data to histogram

    bins : int or list-like, default range(0, 400, 5)
        The number of bins in the histogram or a sequence of bin edges

    underflow_lim : int, default 30
        The minimum number of characters expected in any string

    overflow_lim : int, default 300
        The maximum number of characters expected in any string

    show_under_over : bool
        Show under- and overflow boundaries on the plot and print the
        number of strings outside those limits

    drop_nulls : bool, default True
        Remove null values from the data set read from the file.

    title : str, default 'Lengths of entries'
        Title for the histogram plot

    xlabel : str, default 'Number of characters in an entry'
        Horizontal axis label

    ylabel : str, default 'Number of entries found'
        Vertical axis label

    Returns
    -------
    total : int
        total number of strings

    underflow_count : int
        number of strings shorter than the underflow limit

    overflow_count : int
        number of strings longer than the overflow limit

    fig : matplotlib.axes._subplots.AxesSubplot
        matplotlib axes object for the histogram
    '''

    strings = pd.read_csv(path, header=None)[0]

    if drop_nulls:
        strings = strings.loc[~strings.isna()]

    lengths = strings.map(len)
    fig = lengths.hist(bins=bins, figsize=(12, 6))
    fig.set_xlabel(xlabel)
    fig.set_ylabel(ylabel)
    fig.set_title(title)

    total = lengths.size
    underflow_count = lengths.loc[lengths <= underflow_lim].size
    overflow_count = lengths.loc[lengths >= overflow_lim].size

    if show_over_under:

        fig.axvline(underflow_lim, color='orange', zorder=0)
        fig.axvline(overflow_lim, color='orange', zorder=0)

        ylim = fig.get_ylim()

        xmax = fig.get_xlim()[1]
        fig.set_xlim(0, xmax)
        fig.set_ylim(ylim)

        underflow_fill_xbounds = [0, 0, underflow_lim, underflow_lim]
        underflow_fill_ybounds = [0, ylim[1], ylim[1], 0]
        fig.fill(
            underflow_fill_xbounds,
            underflow_fill_ybounds,
            color='orange',
            alpha=0.5,
            zorder=0
        )

        overflow_fill_x = [overflow_lim, overflow_lim, xmax, xmax]
        overflow_fill_y = [0, ylim[1], ylim[1], 0]
        fig.fill(
            overflow_fill_x,
            overflow_fill_y,
            color='orange',
            alpha=0.5,
            zorder=0
        )

        print(f'total number of strings: {total}')
        print(
            'number of strings shorter than {} characters: {}, {:.1f}%'.format(
                underflow_lim,
                underflow_count,
                100 * underflow_count / total
            )
        )
        print(
            'number of strings within outflow limits: '
            f'{total - underflow_count - overflow_count}'
        )
        print(
            'number of strings longer than {} characters: {}, {:.1f}%'.format(
                overflow_lim,
                overflow_count,
                100 * overflow_count / total
            )
        )

    return total, underflow_count, overflow_count, fig
