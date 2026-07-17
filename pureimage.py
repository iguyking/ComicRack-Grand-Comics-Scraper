'''
Pure-Python image processing for IronPython compatibility.
Implements LANCZOS resampling to match PIL/Pillow exactly.

This module provides ComicTagger-compatible image hashing without
requiring PIL's native C extensions.

Algorithm ported from PIL/Pillow's Resample.c:
https://github.com/python-pillow/Pillow/blob/main/src/libImaging/Resample.c

@author: Local CV Scraper Team
'''

import clr
import math

clr.AddReference('System.Drawing')
from System.Drawing import Bitmap
from System.Drawing.Imaging import PixelFormat


# PIL uses 22 bits of precision for fixed-point math
PRECISION_BITS = 22


def sinc_filter(x):
    '''sinc function: sin(pi*x) / (pi*x)'''
    if x == 0.0:
        return 1.0
    x = x * math.pi
    return math.sin(x) / x


def lanczos_filter(x):
    '''
    LANCZOS3 filter kernel - truncated sinc.
    Matches PIL's lanczos_filter exactly.
    '''
    if -3.0 <= x < 3.0:
        return sinc_filter(x) * sinc_filter(x / 3.0)
    return 0.0


def precompute_coeffs(in_size, in0, in1, out_size, support):
    '''
    Precompute resampling coefficients.
    
    This matches PIL's precompute_coeffs function exactly.
    
    Args:
        in_size: Input dimension size
        in0: Start of input box (usually 0)
        in1: End of input box (usually in_size)
        out_size: Output dimension size
        support: Filter support (3 for LANCZOS3)
    
    Returns:
        (ksize, bounds, kk) where:
        - ksize: maximum kernel size
        - bounds: list of (xmin, xmax) for each output pixel
        - kk: list of coefficient arrays for each output pixel
    '''
    # Scale factor
    scale = float(in1 - in0) / out_size
    filterscale = scale
    if filterscale < 1.0:
        filterscale = 1.0
    
    # Effective support size
    effective_support = support * filterscale
    
    # Maximum kernel size
    ksize = int(math.ceil(effective_support)) * 2 + 1
    
    bounds = []
    kk = []
    
    for xx in range(out_size):
        # Center position in source coordinates
        center = in0 + (xx + 0.5) * scale
        
        # Coefficient scaling factor
        ss = 1.0 / filterscale
        
        # Bounds for this output pixel
        xmin = int(center - effective_support + 0.5)
        if xmin < 0:
            xmin = 0
        xmax = int(center + effective_support + 0.5)
        if xmax > in_size:
            xmax = in_size
        xmax -= xmin  # Now xmax is the count, not the end index
        
        # Calculate coefficients
        k = []
        ww = 0.0
        for x in range(xmax):
            # PIL uses (x + xmin - center + 0.5) * ss
            w = lanczos_filter((x + xmin - center + 0.5) * ss)
            k.append(w)
            ww += w
        
        # Normalize coefficients
        if ww != 0.0:
            k = [w / ww for w in k]
        
        # Pad to ksize with zeros
        while len(k) < ksize:
            k.append(0.0)
        
        bounds.append((xmin, xmax))
        kk.append(k)
    
    return ksize, bounds, kk


def clip8(value):
    '''Clip value to 0-255 range using PIL's rounding.'''
    # PIL uses >> PRECISION_BITS to convert from fixed-point
    # For floating point, we round and clip
    if value < 0:
        return 0
    if value > 255:
        return 255
    return int(value + 0.5)


def resize_lanczos_horizontal(src, src_width, src_height, dst_width, channels):
    '''
    Horizontal pass of LANCZOS resize.
    
    Args:
        src: 2D array of pixel values (row-major, each pixel is value or [R,G,B])
        src_width: Source width
        src_height: Source height
        dst_width: Target width
        channels: 1 for grayscale, 3 for RGB
    
    Returns:
        2D array of horizontally resized pixels
    '''
    support = 3.0  # LANCZOS3
    ksize, bounds, kk = precompute_coeffs(src_width, 0, src_width, dst_width, support)
    
    result = []
    for y in range(src_height):
        row = []
        for xx in range(dst_width):
            xmin, xmax = bounds[xx]
            k = kk[xx]
            
            if channels == 1:
                ss = 0.0
                for x in range(xmax):
                    ss += src[y][x + xmin] * k[x]
                row.append(ss)
            else:
                ss = [0.0] * channels
                for x in range(xmax):
                    for c in range(channels):
                        ss[c] += src[y][x + xmin][c] * k[x]
                row.append(ss)
        result.append(row)
    
    return result


def resize_lanczos_vertical(src, src_width, src_height, dst_height, channels):
    '''
    Vertical pass of LANCZOS resize.
    
    Args:
        src: 2D array from horizontal pass
        src_width: Width (already resized)
        src_height: Source height (original)
        dst_height: Target height
        channels: 1 for grayscale, 3 for RGB
    
    Returns:
        2D array of fully resized pixels (clipped to 0-255)
    '''
    support = 3.0  # LANCZOS3
    ksize, bounds, kk = precompute_coeffs(src_height, 0, src_height, dst_height, support)
    
    result = []
    for yy in range(dst_height):
        ymin, ymax = bounds[yy]
        k = kk[yy]
        
        row = []
        for xx in range(src_width):
            if channels == 1:
                ss = 0.0
                for y in range(ymax):
                    ss += src[y + ymin][xx] * k[y]
                row.append(clip8(ss))
            else:
                ss = [0.0] * channels
                for y in range(ymax):
                    for c in range(channels):
                        ss[c] += src[y + ymin][xx][c] * k[y]
                row.append([clip8(v) for v in ss])
        result.append(row)
    
    return result


def resize_lanczos(pixels, src_width, src_height, dst_width, dst_height, channels=1):
    '''
    Resize image using LANCZOS3 resampling (matches PIL exactly).
    
    This is a two-pass algorithm: horizontal then vertical.
    Ported from PIL/Pillow's Resample.c.
    
    Args:
        pixels: Flat list of pixel values (grayscale or interleaved RGB)
        src_width: Source image width
        src_height: Source image height
        dst_width: Destination width
        dst_height: Destination height
        channels: Number of channels (1 for grayscale, 3 for RGB)
    
    Returns:
        Flat list of resized pixel values
    '''
    # Convert flat list to 2D for easier processing
    src = []
    for y in range(src_height):
        row = []
        for x in range(src_width):
            idx = (y * src_width + x) * channels
            if channels == 1:
                row.append(float(pixels[idx]))
            else:
                row.append([float(pixels[idx + c]) for c in range(channels)])
        src.append(row)
    
    # Two-pass resize: horizontal then vertical
    temp = resize_lanczos_horizontal(src, src_width, src_height, dst_width, channels)
    final = resize_lanczos_vertical(temp, dst_width, src_height, dst_height, channels)
    
    # Flatten result
    result = []
    for row in final:
        for pixel in row:
            if channels == 1:
                result.append(pixel)
            else:
                result.extend(pixel)
    
    return result


def rgb_to_grayscale(r, g, b):
    '''
    Convert RGB to grayscale using standard luminance formula.
    Same formula as PIL's convert("L").
    
    Args:
        r, g, b: RGB values (0-255)
    
    Returns:
        Grayscale value (0-255)
    '''
    # ITU-R BT.601 luma coefficients (same as PIL)
    return int(round(0.299 * r + 0.587 * g + 0.114 * b))


class PureImage(object):
    '''
    Pure-Python image class compatible with PIL's interface.
    Only implements what we need for hashing.
    '''
    
    def __init__(self, width, height, pixels, mode='L'):
        '''
        Create image from pixel data.
        
        Args:
            width: Image width
            height: Image height
            pixels: Flat list of pixel values
            mode: 'L' for grayscale, 'RGB' for color
        '''
        self.width = width
        self.height = height
        self._pixels = list(pixels)
        self.mode = mode
    
    @classmethod
    def from_dotnet_image(cls, dotnet_image):
        '''
        Create PureImage from .NET System.Drawing.Image.
        
        Preserves RGB color data for proper ComicTagger compatibility.
        ahash needs to resize color image FIRST, then convert to grayscale.
        
        Args:
            dotnet_image: .NET Image object
        
        Returns:
            PureImage instance in RGB mode
        '''
        width = dotnet_image.Width
        height = dotnet_image.Height
        
        # Convert to Bitmap if needed
        if not isinstance(dotnet_image, Bitmap):
            bmp = Bitmap(dotnet_image)
        else:
            bmp = dotnet_image
        
        # Extract RGB pixels (interleaved: R, G, B, R, G, B, ...)
        pixels = []
        for y in range(height):
            for x in range(width):
                color = bmp.GetPixel(x, y)
                pixels.append(color.R)
                pixels.append(color.G)
                pixels.append(color.B)
        
        return cls(width, height, pixels, mode='RGB')
    
    def resize(self, size, resample=None):
        '''
        Resize image using pure-Python LANCZOS3 resampling.
        
        This implementation is ported from PIL/Pillow's Resample.c to produce
        identical results for hash matching with ComicTagger.
        
        Args:
            size: Tuple of (width, height)
            resample: Ignored (always uses LANCZOS3)
        
        Returns:
            New PureImage with resized content (same mode as input)
        '''
        dst_width, dst_height = size
        
        if self.mode == 'RGB':
            channels = 3
        else:
            channels = 1
        
        # Use our PIL-compatible LANCZOS implementation
        resized_pixels = resize_lanczos(
            self._pixels, 
            self.width, self.height, 
            dst_width, dst_height, 
            channels
        )
        
        return PureImage(dst_width, dst_height, resized_pixels, mode=self.mode)
    
    def convert(self, mode):
        '''
        Convert image to different mode.
        
        Args:
            mode: Target mode ('L' for grayscale)
        
        Returns:
            New PureImage in target mode
        '''
        if mode == self.mode:
            return PureImage(self.width, self.height, self._pixels, self.mode)
        
        if mode == 'L' and self.mode == 'RGB':
            # RGB to grayscale
            gray_pixels = []
            for i in range(0, len(self._pixels), 3):
                r, g, b = self._pixels[i:i+3]
                gray_pixels.append(rgb_to_grayscale(r, g, b))
            return PureImage(self.width, self.height, gray_pixels, mode='L')
        
        raise ValueError("Unsupported conversion: %s to %s" % (self.mode, mode))
    
    def getdata(self):
        '''
        Get pixel data as a flat list.
        
        Returns:
            List of pixel values
        '''
        return self._pixels


# Compatibility shim for PIL.Image.Resampling
class Resampling(object):
    LANCZOS = 'lanczos'