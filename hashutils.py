'''
This module provides hash utilities for matching comics using MD5 and 
perceptual hashing algorithms compatible with ComicTagger.

Implements:
- MD5 hashing for files and images
- ComicTagger-compatible average hash (ct_ahash)
- ComicTagger-compatible perceptual hash (ct_phash)

Uses pure-Python LANCZOS resampling for exact ComicTagger compatibility.
The PIL module is bundled with the plugin.

@author: Local CV Scraper Team(original)/Adapted by Strumples and Gemini
for use with Grand Comics Database
'''

import clr
import math

clr.AddReference('System')
from System import Array, Byte
from System.IO import File, FileStream, FileMode, MemoryStream
from System.Security.Cryptography import MD5

# Import our pure-Python PIL implementation
_PIL_AVAILABLE = False
_PIL_ERROR = None
try:
    # Try importing PIL directly - it should be in sys.path already
    # or we'll add it manually
    import sys
    
    # Try direct import first
    try:
        import gcd_log as hash_log
        hash_log.debug("Attempting to import PIL...")
        from PIL import Image as PILImage
        _PIL_AVAILABLE = True
        hash_log.debug("PIL imported successfully!")
    except ImportError as ex:
        _PIL_ERROR = "ImportError: " + str(ex)
        hash_log.debug("PIL import failed: " + str(ex))
        
        # Try to add PIL to path using various methods
        # Method 1: Try using db module's path (it's in the parent directory)
        try:
            hash_log.debug("Trying to find PIL via db module path...")
            import db as db_module
            if hasattr(db_module, '__file__'):
                clr.AddReference('System')
                from System.IO import Directory, Path as SysPath
                db_dir = Directory.GetParent(db_module.__file__).FullName
                _pil_dir = SysPath.Combine(db_dir, 'PIL')
                hash_log.debug("Checking PIL dir: " + _pil_dir)
                if Directory.Exists(_pil_dir):
                    if _pil_dir not in sys.path:
                        sys.path.insert(0, _pil_dir)
                        hash_log.debug("Added PIL to path: " + _pil_dir)
                    from PIL import Image as PILImage
                    _PIL_AVAILABLE = True
                    hash_log.debug("PIL imported via db module path!")
                else:
                    hash_log.debug("PIL directory does not exist: " + _pil_dir)
        except Exception as ex2:
            _PIL_ERROR = "Method 1 failed: " + str(ex2)
            hash_log.debug("Method 1 failed: " + str(ex2))
        
        # Method 2: Try relative to current directory
        if not _PIL_AVAILABLE:
            try:
                hash_log.debug("Trying to find PIL via current directory...")
                clr.AddReference('System')
                from System.IO import Directory, Path as SysPath
                this_dir = Directory.GetCurrentDirectory()
                _pil_dir = SysPath.Combine(this_dir, 'PIL')
                hash_log.debug("Checking PIL dir: " + _pil_dir)
                if Directory.Exists(_pil_dir):
                    if _pil_dir not in sys.path:
                        sys.path.insert(0, _pil_dir)
                        hash_log.debug("Added PIL to path: " + _pil_dir)
                    from PIL import Image as PILImage
                    _PIL_AVAILABLE = True
                    hash_log.debug("PIL imported via current directory!")
                else:
                    hash_log.debug("PIL directory does not exist: " + _pil_dir)
            except Exception as ex3:
                _PIL_ERROR = "Method 2 failed: " + str(ex3)
                hash_log.debug("Method 2 failed: " + str(ex3))

        # Method 3: ComicRack's package installer flattens subdirectories,
        # so pureimage.py may sit directly in the plugin folder
        if not _PIL_AVAILABLE:
            try:
                hash_log.debug("Trying flat pureimage module...")
                from pureimage import PureImage as PILImage, Resampling
                PILImage.Resampling = Resampling
                _PIL_AVAILABLE = True
                hash_log.debug("pureimage imported directly!")
            except Exception as ex4:
                _PIL_ERROR = "Method 3 failed: " + str(ex4)
                hash_log.debug("Method 3 failed: " + str(ex4))
    except Exception as ex_outer:
        _PIL_ERROR = "Outer exception: " + str(ex_outer)

except Exception as ex:
    _PIL_AVAILABLE = False
    _PIL_ERROR = "Top-level exception: " + str(ex)

if not _PIL_AVAILABLE:
    try:
        import log
        log.debug("WARNING: PIL not available - perceptual hash matching will be disabled")
        if _PIL_ERROR:
            log.debug("PIL error details: " + _PIL_ERROR)
    except:
        pass


#==============================================================================
# MD5 Hash Functions
#==============================================================================

def calculate_file_md5(filepath):
    '''
    Calculate MD5 hash of an entire file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        MD5 hash as lowercase hex string, or None on error
    '''
    try:
        md5 = MD5.Create()
        with FileStream(filepath, FileMode.Open) as stream:
            hash_bytes = md5.ComputeHash(stream)
            return ''.join('%02x' % b for b in hash_bytes)
    except Exception:
        return None


def calculate_image_md5(image):
    '''
    Calculate MD5 hash of a .NET Image object's raw pixel data.
    
    Note: This calculates MD5 of the pixel data, not the file bytes.
    For first page MD5 matching against the database, you typically want
    calculate_bytes_md5() on the raw image file bytes.
    
    Args:
        image: .NET System.Drawing.Image object
        
    Returns:
        MD5 hash as lowercase hex string, or None on error
    '''
    try:
        # Save image to memory stream and hash those bytes
        ms = MemoryStream()
        image.Save(ms, image.RawFormat)
        ms.Position = 0
        
        md5 = MD5.Create()
        hash_bytes = md5.ComputeHash(ms)
        ms.Close()
        
        return ''.join('%02x' % b for b in hash_bytes)
    except Exception:
        return None


def calculate_bytes_md5(data):
    '''
    Calculate MD5 hash of raw bytes.
    
    Args:
        data: Byte array or .NET Array[Byte]
        
    Returns:
        MD5 hash as lowercase hex string, or None on error
    '''
    try:
        md5 = MD5.Create()
        if isinstance(data, str):
            # IronPython 2.7 string of bytes
            data = Array[Byte]([Byte(ord(c)) for c in data])
        hash_bytes = md5.ComputeHash(data)
        return ''.join('%02x' % b for b in hash_bytes)
    except Exception:
        return None


#==============================================================================
# Image Conversion Helpers
#==============================================================================

def _dotnet_image_to_pil(dotnet_image):
    '''
    Convert a .NET System.Drawing.Image to a PIL-compatible Image.
    
    Uses our pure-Python PureImage class for IronPython compatibility.
    
    Args:
        dotnet_image: .NET System.Drawing.Image object
        
    Returns:
        PureImage object compatible with PIL interface, or None on error
    '''
    if not _PIL_AVAILABLE:
        return None
    
    try:
        # Use our pure-Python image class
        return PILImage.from_dotnet_image(dotnet_image)
    except Exception as ex:
        import log
        log.debug_exc("_dotnet_image_to_pil error: " + str(ex))
        return None


def is_pil_available():
    '''Check if PIL is available for perceptual hashing.'''
    return _PIL_AVAILABLE


#==============================================================================
# ComicTagger-Compatible Perceptual Hash Functions  
#==============================================================================

class CTImageHasher(object):
    '''
    ComicTagger-compatible image hasher using PIL/Pillow.
    
    Implements the exact same algorithms as ComicTagger's ImageHasher class.
    
    Provides:
    - average_hash(): Simple mean-based hash (fast, good for exact duplicates)
    - perception_hash(): DCT-based hash (slower, better for similar images)
    '''
    
    def __init__(self, image, width=8, height=8):
        '''
        Initialize hasher with a .NET Image or PIL Image.
        
        Args:
            image: .NET System.Drawing.Image or PIL Image object
            width: Width for average hash resize (default: 8)
            height: Height for average hash resize (default: 8)
        '''
        self.width = width
        self.height = height
        
        if not _PIL_AVAILABLE:
            self.image = None
            return
        
        # Convert .NET image to PIL if needed
        if hasattr(image, 'resize'):
            # Already a PIL image
            self.image = image
        else:
            # .NET image, convert to PIL
            self.image = _dotnet_image_to_pil(image)
    
    def average_hash(self):
        '''
        Calculate average hash using ComicTagger's algorithm.
        
        Algorithm:
        1. Resize image to 8x8 pixels using LANCZOS
        2. Convert to grayscale
        3. Calculate mean pixel value
        4. Create 64-bit hash: bit is 1 if pixel > mean, 0 otherwise
        
        Returns:
            64-bit integer hash, or 0 on error
        '''
        if self.image is None:
            return 0
        
        try:
            # Resize with LANCZOS and convert to grayscale (exact ComicTagger match)
            # For ahash: resize RGB first, then convert to grayscale
            resized = self.image.resize((self.width, self.height), PILImage.Resampling.LANCZOS)
            image = resized.convert("L")
            pixels = list(image.getdata())
            
            # Calculate mean (IronPython 2.7 compatible)
            avg = sum(pixels) / float(len(pixels))
            
            # Build hash: bit is 1 if pixel > average
            h = 0
            for i, p in enumerate(pixels):
                if p > avg:
                    h |= 1 << (len(pixels) - 1 - i)
            
            return h & 0xFFFFFFFFFFFFFFFF
            
        except Exception as ex:
            import log
            log.debug_exc("average_hash error: " + str(ex))
            return 0
    
    def perception_hash(self):
        '''
        Calculate perceptual hash using ComicTagger's DCT-based algorithm.
        
        Algorithm:
        1. Resize image to 32x32 pixels and convert to grayscale
        2. Perform 2D Discrete Cosine Transform (DCT)
        3. Extract low-frequency 8x8 block (top-left corner of DCT)
        4. Calculate median of these 64 values
        5. Create 64-bit hash: bit is 1 if value > median, 0 otherwise
        
        Returns:
            64-bit integer hash, or 0 on error
        '''
        if self.image is None:
            return 0
        
        try:
            highfreq_factor = 4
            img_size = 8 * highfreq_factor  # 32
            
            # Convert to grayscale and resize with LANCZOS (exact ComicTagger match)
            image = self.image.convert("L").resize((img_size, img_size), PILImage.Resampling.LANCZOS)
            flat_pixels = list(image.getdata())
            
            # Convert to 32x32 2D array
            pixels = []
            for row in range(img_size):
                x = row * img_size
                pixels.append(flat_pixels[x:x + img_size])
            
            # Apply 2D DCT (first rows, then columns)
            dct = self._generate_dct2(self._generate_dct2(pixels, axis=0), axis=1)
            
            # Extract top-left 8x8 low-frequency block
            dctlowfreq = []
            for row in dct[:8]:
                dctlowfreq.extend(row[:8])
            
            # Calculate median
            med = self._median(dctlowfreq)
            
            # Build hash: bit is 1 if DCT value > median
            h = 0
            for i, p in enumerate(dctlowfreq):
                if p > med:
                    h |= 1 << (len(dctlowfreq) - 1 - i)
            
            return h & 0xFFFFFFFFFFFFFFFF
            
        except Exception as ex:
            import log
            log.debug_exc("perception_hash error: " + str(ex))
            return 0
    
    def _generate_dct2(self, block, axis=0):
        '''
        Perform 2D Discrete Cosine Transform on a 2D block.
        
        Args:
            block: 2D list of pixel values
            axis: 0 for row-wise DCT, 1 for column-wise DCT
            
        Returns:
            2D list with DCT coefficients
        '''
        def dct1(block):
            '''Perform 1D Discrete Cosine Transform (DCT) on a given block.'''
            N = len(block)
            dct_block = [0.0] * N
            for k in range(N):
                sum_val = 0.0
                for n in range(N):
                    cos_val = math.cos(math.pi * k * (2 * n + 1) / (2 * N))
                    sum_val += block[n] * cos_val
                dct_block[k] = sum_val
            return dct_block
        
        rows = len(block)
        cols = len(block[0])
        dct_block = [[0.0] * cols for _ in range(rows)]
        
        if axis == 0:
            # Apply DCT to each row
            for i in range(rows):
                dct_block[i] = dct1(block[i])
        elif axis == 1:
            # Apply DCT to each column
            for j in range(cols):
                column = [block[i][j] for i in range(rows)]
                dct_column = dct1(column)
                for i in range(rows):
                    dct_block[i][j] = dct_column[i]
        
        return dct_block
    
    def _median(self, values):
        '''
        Calculate median of a list of values.
        IronPython 2.7 compatible (no statistics.median).
        
        Args:
            values: List of numeric values
            
        Returns:
            Median value
        '''
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n % 2 == 1:
            return sorted_values[n // 2]
        else:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2.0


#==============================================================================
# Hamming Distance / Similarity Functions
#==============================================================================

# Pre-compute popcount table for fast Hamming distance (covers bytes 0-255)
__POPCOUNT_TABLE = None

def _init_popcount_table():
    '''Initialize lookup table for bit counting (popcount)'''
    global __POPCOUNT_TABLE
    if __POPCOUNT_TABLE is None:
        __POPCOUNT_TABLE = [0] * 256
        for i in range(256):
            __POPCOUNT_TABLE[i] = (i & 1) + __POPCOUNT_TABLE[i >> 1] if i > 0 else 0

def hamming_distance(hash1, hash2):
    '''
    Calculate Hamming distance between two 64-bit hashes.
    Lower distance = more similar images.
    
    Uses lookup table for fast bit counting.
    
    Args:
        hash1: First 64-bit integer hash
        hash2: Second 64-bit integer hash
        
    Returns:
        Number of differing bits (0-64), or 64 if either hash is None/0
    '''
    if hash1 is None or hash2 is None or hash1 == 0 or hash2 == 0:
        return 64
    
    global __POPCOUNT_TABLE
    if __POPCOUNT_TABLE is None:
        _init_popcount_table()
    
    xor = hash1 ^ hash2
    # Use lookup table - process 8 bits at a time
    return (__POPCOUNT_TABLE[xor & 0xff] +
            __POPCOUNT_TABLE[(xor >> 8) & 0xff] +
            __POPCOUNT_TABLE[(xor >> 16) & 0xff] +
            __POPCOUNT_TABLE[(xor >> 24) & 0xff] +
            __POPCOUNT_TABLE[(xor >> 32) & 0xff] +
            __POPCOUNT_TABLE[(xor >> 40) & 0xff] +
            __POPCOUNT_TABLE[(xor >> 48) & 0xff] +
            __POPCOUNT_TABLE[(xor >> 56) & 0xff])


def hash_similarity(hash1, hash2):
    '''
    Calculate similarity between two hashes as a value between 0.0 and 1.0.
    1.0 = identical, 0.0 = completely different.
    
    Args:
        hash1: First 64-bit integer hash
        hash2: Second 64-bit integer hash
        
    Returns:
        Similarity value (0.0 to 1.0)
    '''
    distance = hamming_distance(hash1, hash2)
    return 1.0 - (distance / 64.0)


#==============================================================================
# Convenience Functions
#==============================================================================

def calculate_image_hashes(image):
    '''
    Calculate both ComicTagger-compatible hashes for an image.
    
    Args:
        image: .NET System.Drawing.Image or PIL Image object
        
    Returns:
        Tuple of (ct_ahash, ct_phash) as integers, or (0, 0) on error/PIL unavailable
    '''
    if not _PIL_AVAILABLE:
        return (0, 0)
    
    try:
        hasher = CTImageHasher(image)
        return (hasher.average_hash(), hasher.perception_hash())
    except Exception:
        return (0, 0)


def calculate_all_hashes_from_image(image):
    '''
    Calculate all hash types for an image.
    
    Args:
        image: .NET System.Drawing.Image or PIL Image object
        
    Returns:
        Dictionary with 'ct_ahash' and 'ct_phash' keys
    '''
    ct_ahash, ct_phash = calculate_image_hashes(image)
    return {
        'ct_ahash': ct_ahash,
        'ct_phash': ct_phash
    }
