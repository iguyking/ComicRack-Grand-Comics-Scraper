'''
PIL compatibility module for IronPython.

This package provides ComicTagger-compatible image hashing using 
pure-Python implementations that work in IronPython without native extensions.

Usage:
    from PIL import Image
    img = Image.from_dotnet_image(dotnet_image)
    resized = img.resize((8, 8), Image.Resampling.LANCZOS)
'''

try:
    from pureimage import PureImage as Image
    from pureimage import Resampling
    # Make Image class have Resampling attribute like PIL
    Image.Resampling = Resampling
except ImportError:
    # Fallback if pureimage can't be found
    Image = None
    Resampling = None
