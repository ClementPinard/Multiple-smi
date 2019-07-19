import cairo
import numpy as np
from colorspacious import cspace_convert
from itertools import cycle


def get_default_colors(ratio=1.2):
    '''Automatically setup colors for each machines without specified color,
    with optimized palette for better identification, colors taken from matplotlib 2.0'''
    default_colors = np.array([
        [31, 119, 180],
        [255, 127, 14],
        [44, 160, 44],
        [214, 39, 40],
        [148, 103, 189],
        [140, 86, 75],
        [227, 119, 194],
        [127, 127, 127],
        [188, 189, 34],
        [23, 190, 207]
    ])
    '''First variation needs to be more saturated and darker
    second needs to be less saturated and lighter'''
    JCh_default = cspace_convert(default_colors, "sRGB255", "JCh")
    JCh_1 = JCh_default * np.array([[1/ratio, ratio, 1]])
    JCh_2 = JCh_default * np.array([[ratio, 1/ratio, 1]])
    default_colors = np.stack((cspace_convert(JCh_1, "JCh", "sRGB255"),
                               cspace_convert(JCh_2, "JCh", "sRGB255")), axis=1)
    return default_colors.astype(np.int32).clip(0, 255)


DEFAULT_COLORS = cycle(get_default_colors())


def draw_icon(machine):
    '''Draws a graph with 2 columns 1 for each percentage (1 is full, 0 is empty)'''
    if 'colors' in machine.keys():
        color1, color2 = machine['colors']
    else:
        color1, color2 = next(DEFAULT_COLORS)
        machine['colors'] = [color1, color2]
    WIDTH, HEIGHT = 22, 22
    summary = machine['summary']
    if summary['nGPUs'] > 2:
        WIDTH = 11*summary['nGPUs']  # if more than 1 GPU on a machine, each column is 11px wide (and not 22px)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)
    if summary['nGPUs'] > 0:
        ctx.scale(WIDTH/summary['nGPUs'], HEIGHT)  # Normalizing the canvas coordinates go from (0,0) to (nGPUs,1)

    for i in range(summary['nGPUs']):
        gpu = summary['GPUs'][i]
        percentage1, percentage2 = gpu['utilization']/100, gpu['used_mem']/gpu['memory']
        ctx.rectangle(i, 1-percentage1, 0.5, percentage1)  # Rectangle(x0, y0, x1, y1)
        ctx.set_source_rgb(color1[0]/255, color1[1]/255, color1[2]/255)
        ctx.fill()

        ctx.rectangle(i + 0.5, 1 - percentage2, 0.5, percentage2)  # Rectangle(x0, y0, x1, y1)
        ctx.set_source_rgb(color2[0]/255, color2[1]/255, color2[2]/255)
        ctx.fill()
    return(surface)
