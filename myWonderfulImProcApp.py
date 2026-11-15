import sys
import math
from PIL import Image

######################
# FUNCTION DEFINITIONS
######################

def doBrightness(pixels, param):
    value = float(param)
    result = []
    for pixel in pixels:
        if isinstance(pixel, tuple):
            # We use max(0, min(255, ...)) to clip the values.
            # This prevents pixel values from exceeding 255 or dropping below 0, 
            # which would cause image corruption or artifacts.
            new_pixel = tuple(max(0, min(255, int(channel + value))) for channel in pixel)
        else:
            new_pixel = max(0, min(255, int(pixel + value)))
        result.append(new_pixel)
    return result

def doContrast(pixels, param):
    factor = float(param)
    result = []
    if factor < 0:
        raise ValueError("Contrast factor cannot be negative !")
    for pixel in pixels:
        if isinstance(pixel, tuple):
            # We center the pixel value around 128 (middle gray) before applying the factor.
            # This ensures that light colors get lighter and dark colors get darker symmetrically.
            new_pixel = tuple(max(0, min(255, int((channel - 128) * factor + 128))) for channel in pixel)
        else:
            new_pixel = max(0, min(255, int((pixel - 128) * factor + 128)))
        result.append(new_pixel)
    return result

def doNegative(pixels):
    result = []
    for pixel in pixels:
        if isinstance(pixel, tuple):
            new_pixel = tuple(255 - channel for channel in pixel)
        else:
            new_pixel = 255 - pixel
        result.append(new_pixel)
    return result

def doHflip(pixels, width, height):
    result = []
    for y in range(height):
        # Find the index of the last pixel in the current row
        row_end_index = (y * width) + width - 1
        for x in range(width):
            # Walk backwards through the row
            pixel = pixels[row_end_index - x]
            result.append(pixel)
    return result

def doVflip(pixels, width, height):
    result = []
    for y in range(height):
        # Map the current top row to the corresponding bottom row
        bottom_y = (height - 1) - y
        row_start_index = bottom_y * width
        for x in range(width):
            pixel = pixels[row_start_index + x]
            result.append(pixel)
    return result


def doDflip(pixels, width, height):
    result = []
    for y in range(height):
        # Map to the corresponding bottom row
        bottom_y = (height - 1) - y
        for x in range(width):
            # Map to the corresponding rightmost pixel
            right_x = (width - 1) - x

            # Calculate the 1D index for the target pixel
            old_index = (bottom_y * width) + right_x
            result.append(pixels[old_index])
    return result

def doShrink(pixels, width, height, param):
    factor = int(param)
    if factor <= 0:
        raise ValueError("Shrink factor must be greater than 0!")
        
    result = []
    new_width = width // factor
    new_height = height // factor
    is_rgb = isinstance(pixels[0], tuple)
    
    # Interpolation par Moyenne de bloc (Block Averaging)
    # On calcule la moyenne de tous les pixels dans le bloc factor x factor
    for y in range(new_height):
        for x in range(new_width):
            
            if is_rgb:
                sum_r, sum_g, sum_b = 0, 0, 0
                count = 0
                for dy in range(factor):
                    for dx in range(factor):
                        old_y = (y * factor) + dy
                        old_x = (x * factor) + dx
                        pixel = pixels[old_y * width + old_x]
                        sum_r += pixel[0]
                        sum_g += pixel[1]
                        sum_b += pixel[2]
                        count += 1
                result.append((int(sum_r/count), int(sum_g/count), int(sum_b/count)))
            else:
                sum_v = 0
                count = 0
                for dy in range(factor):
                    for dx in range(factor):
                        old_y = (y * factor) + dy
                        old_x = (x * factor) + dx
                        sum_v += pixels[old_y * width + old_x]
                        count += 1
                result.append(int(sum_v/count))
                
    return result, new_width, new_height

def doShrink(pixels, width, height, param):
    factor = int(param)
    if factor <= 0:
        raise ValueError("Shrink factor must be greater than 0!")
        
    result = []
    new_width = width // factor
    new_height = height // factor
    is_rgb = isinstance(pixels[0], tuple)
    
    # Block Averaging Interpolation
    # Calculate the average of all pixels within the factor x factor block
    for y in range(new_height):
        for x in range(new_width):
            
            if is_rgb:
                sum_r, sum_g, sum_b = 0, 0, 0
                count = 0
                for dy in range(factor):
                    for dx in range(factor):
                        old_y = (y * factor) + dy
                        old_x = (x * factor) + dx
                        pixel = pixels[old_y * width + old_x]
                        sum_r += pixel[0]
                        sum_g += pixel[1]
                        sum_b += pixel[2]
                        count += 1
                result.append((int(sum_r/count), int(sum_g/count), int(sum_b/count)))
            else:
                sum_v = 0
                count = 0
                for dy in range(factor):
                    for dx in range(factor):
                        old_y = (y * factor) + dy
                        old_x = (x * factor) + dx
                        sum_v += pixels[old_y * width + old_x]
                        count += 1
                result.append(int(sum_v/count))
                
    return result, new_width, new_height

def doEnlarge(pixels, width, height, param):
    factor = int(param)
    if factor <= 0:
        raise ValueError("Enlarge factor must be greater than 0!")
        
    result = []
    new_width = width * factor
    new_height = height * factor
    is_rgb = isinstance(pixels[0], tuple)
    
    # Bilinear Interpolation
    for y in range(new_height):
        for x in range(new_width):
            # Calculate the corresponding floating-point coordinates in the original image
            old_x = x / factor
            old_y = y / factor
            
            # Get the coordinates of the 4 nearest neighboring pixels
            x1 = int(old_x)
            y1 = int(old_y)
            x2 = min(x1 + 1, width - 1)
            y2 = min(y1 + 1, height - 1)
            
            # Weights for the interpolation
            dx = old_x - x1
            dy = old_y - y1
            
            # The 4 neighboring pixels
            p11 = pixels[y1 * width + x1] # Top Left
            p21 = pixels[y1 * width + x2] # Top Right
            p12 = pixels[y2 * width + x1] # Bottom Left
            p22 = pixels[y2 * width + x2] # Bottom Right
            
            if is_rgb:
                new_pixel = []
                # Apply the bilinear formula for each color channel
                for c in range(3):
                    top = p11[c] * (1 - dx) + p21[c] * dx
                    bottom = p12[c] * (1 - dx) + p22[c] * dx
                    val = top * (1 - dy) + bottom * dy
                    new_pixel.append(int(val))
                result.append(tuple(new_pixel))
            else:
                top = p11 * (1 - dx) + p21 * dx
                bottom = p12 * (1 - dx) + p22 * dx
                val = top * (1 - dy) + bottom * dy
                result.append(int(val))
                
    return result, new_width, new_height

def doMin(pixels, width, height, param):
    window_size = int(param)
    if window_size % 2 == 0 or window_size < 3:
        raise ValueError("Window size must be an odd integer >= 3")
        
    result = []
    is_rgb = isinstance(pixels[0], tuple)
    offset = window_size // 2
    
    for y in range(height):
        for x in range(width):
            window = []
            
            # Extract local window. 
            # We use clamping (max(0, min(limit, val))) to handle image borders.
            # If the window goes out of bounds, it replicates the edge pixel to prevent IndexError.
            for wy in range(y - offset, y + offset + 1):
                cy = max(0, min(height - 1, wy))
                for wx in range(x - offset, x + offset + 1):
                    cx = max(0, min(width - 1, wx))
                    window.append(pixels[cy * width + cx])
            
            if is_rgb:
                r_min = min(p[0] for p in window)
                g_min = min(p[1] for p in window)
                b_min = min(p[2] for p in window)
                result.append((r_min, g_min, b_min))
            else:
                result.append(min(window))
                
    return result

def doMax(pixels, width, height, param):
    window_size = int(param)
    if window_size % 2 == 0 or window_size < 3:
        raise ValueError("Window size must be an odd integer >= 3")
        
    result = []
    is_rgb = isinstance(pixels[0], tuple)
    offset = window_size // 2
    
    for y in range(height):
        for x in range(width):
            window = []
            
            # Border clamping logic applied here as well
            for wy in range(y - offset, y + offset + 1):
                cy = max(0, min(height - 1, wy))
                for wx in range(x - offset, x + offset + 1):
                    cx = max(0, min(width - 1, wx))
                    window.append(pixels[cy * width + cx])
            
            if is_rgb:
                r_max = max(p[0] for p in window)
                g_max = max(p[1] for p in window)
                b_max = max(p[2] for p in window)
                result.append((r_max, g_max, b_max))
            else:
                result.append(max(window))
                
    return result

def doAdaptive(pixels, width, height, param):
    s_max = int(param)
    if s_max % 2 == 0 or s_max < 3:
        raise ValueError("Maximum window size (Smax) must be an odd integer >= 3")
        
    result = []
    is_rgb = isinstance(pixels[0], tuple)
    
    # Internal function to process one coordinate
    def adaptive_process(x, y, channel_idx=None):
        window_size = 3
        
        while window_size <= s_max:
            offset = window_size // 2
            window = []
            
            # Border clamping to extract window
            for wy in range(y - offset, y + offset + 1):
                cy = max(0, min(height - 1, wy))
                for wx in range(x - offset, x + offset + 1):
                    cx = max(0, min(width - 1, wx))
                    val = pixels[cy * width + cx]
                    
                    if channel_idx is not None:
                        window.append(val[channel_idx])
                    else:
                        window.append(val)
            
            z_min = min(window)
            z_max = max(window)
            sorted_window = sorted(window)
            z_med = sorted_window[len(sorted_window) // 2]
            
            pixel_val = pixels[y * width + x]
            z_xy = pixel_val[channel_idx] if channel_idx is not None else pixel_val
            
            # STAGE A: Check if the median itself is an impulse noise
            A1 = z_med - z_min
            A2 = z_med - z_max
            
            if A1 > 0 and A2 < 0:
                # STAGE B: The median is good. Now check if the center pixel is noise
                B1 = z_xy - z_min
                B2 = z_xy - z_max
                if B1 > 0 and B2 < 0:
                    # The pixel is not noise
                    # We return the ORIGINAL pixel to preserve image sharpness
                    return z_xy
                else:
                    # The pixel is noise. Replace it with median
                    return z_med
            else:
                # The median is noise, increase window size and try again
                window_size += 2
                
        # If maximum window size is reached, return the original value
        pixel_val = pixels[y * width + x]
        return pixel_val[channel_idx] if channel_idx is not None else pixel_val

    for y in range(height):
        for x in range(width):
            if is_rgb:
                # Process each color channel independently
                new_pixel = (
                    adaptive_process(x, y, 0), # Red
                    adaptive_process(x, y, 1), # Green
                    adaptive_process(x, y, 2)  # Blue
                )
                result.append(new_pixel)
            else:
                result.append(adaptive_process(x, y, None))
                
    return result

def doMSE(pixels1, pixels2):
    if len(pixels1) != len(pixels2):
        raise ValueError("Images must have the exact same dimensions for comparison.")
        
    MN = len(pixels1)
    
    if isinstance(pixels1[0], tuple):
        # Calculate MSE for R, G, and B channels separately
        mse_r = sum((p1[0] - p2[0]) ** 2 for p1, p2 in zip(pixels1, pixels2)) / MN
        mse_g = sum((p1[1] - p2[1]) ** 2 for p1, p2 in zip(pixels1, pixels2)) / MN
        mse_b = sum((p1[2] - p2[2]) ** 2 for p1, p2 in zip(pixels1, pixels2)) / MN
        return (mse_r, mse_g, mse_b)
    else:
        # Grayscale
        mse = sum((v1 - v2) ** 2 for v1, v2 in zip(pixels1, pixels2)) / MN
        return mse

def doPMSE(pixels1, pixels2):
    if len(pixels1) != len(pixels2):
        raise ValueError("Images must have the exact same dimensions for comparison.")
        
    MN = len(pixels1)
    
    if isinstance(pixels1[0], tuple):
        sse_r = sum((p1[0] - p2[0]) ** 2 for p1, p2 in zip(pixels1, pixels2))
        sse_g = sum((p1[1] - p2[1]) ** 2 for p1, p2 in zip(pixels1, pixels2))
        sse_b = sum((p1[2] - p2[2]) ** 2 for p1, p2 in zip(pixels1, pixels2))
        
        max_r = max(p[0] for p in pixels1)
        max_g = max(p[1] for p in pixels1)
        max_b = max(p[2] for p in pixels1)
        
        pmse_r = (sse_r / MN) / (max_r ** 2) if max_r != 0 else float('inf')
        pmse_g = (sse_g / MN) / (max_g ** 2) if max_g != 0 else float('inf')
        pmse_b = (sse_b / MN) / (max_b ** 2) if max_b != 0 else float('inf')
        
        return (pmse_r, pmse_g, pmse_b)
    else:
        sse = sum((v1 - v2) ** 2 for v1, v2 in zip(pixels1, pixels2))
        max_f = max(pixels1)
        if max_f == 0:
            return float('inf')
        return (sse / MN) / (max_f ** 2)

def doSNR(pixels1, pixels2):
    if len(pixels1) != len(pixels2):
        raise ValueError("Images must have the exact same dimensions for comparison.")
        
    if isinstance(pixels1[0], tuple):
        sse_r = sum((p1[0] - p2[0]) ** 2 for p1, p2 in zip(pixels1, pixels2))
        sse_g = sum((p1[1] - p2[1]) ** 2 for p1, p2 in zip(pixels1, pixels2))
        sse_b = sum((p1[2] - p2[2]) ** 2 for p1, p2 in zip(pixels1, pixels2))
        
        sum_sq_r = sum(p[0] ** 2 for p in pixels1)
        sum_sq_g = sum(p[1] ** 2 for p in pixels1)
        sum_sq_b = sum(p[2] ** 2 for p in pixels1)
        
        snr_r = 10 * math.log10(sum_sq_r / sse_r) if sse_r != 0 else float('inf')
        snr_g = 10 * math.log10(sum_sq_g / sse_g) if sse_g != 0 else float('inf')
        snr_b = 10 * math.log10(sum_sq_b / sse_b) if sse_b != 0 else float('inf')
        
        return (snr_r, snr_g, snr_b)
    else:
        sse = sum((v1 - v2) ** 2 for v1, v2 in zip(pixels1, pixels2))
        if sse == 0:
            return float('inf')
        sum_sq = sum(v ** 2 for v in pixels1)
        return 10 * math.log10(sum_sq / sse)

def doPSNR(pixels1, pixels2):
    if len(pixels1) != len(pixels2):
        raise ValueError("Images must have the exact same dimensions for comparison.")
        
    MN = len(pixels1)
    
    if isinstance(pixels1[0], tuple):
        sse_r = sum((p1[0] - p2[0]) ** 2 for p1, p2 in zip(pixels1, pixels2))
        sse_g = sum((p1[1] - p2[1]) ** 2 for p1, p2 in zip(pixels1, pixels2))
        sse_b = sum((p1[2] - p2[2]) ** 2 for p1, p2 in zip(pixels1, pixels2))
        
        max_r = max(p[0] for p in pixels1)
        max_g = max(p[1] for p in pixels1)
        max_b = max(p[2] for p in pixels1)
        
        psnr_r = 10 * math.log10((MN * (max_r ** 2)) / sse_r) if sse_r != 0 else float('inf')
        psnr_g = 10 * math.log10((MN * (max_g ** 2)) / sse_g) if sse_g != 0 else float('inf')
        psnr_b = 10 * math.log10((MN * (max_b ** 2)) / sse_b) if sse_b != 0 else float('inf')
        
        return (psnr_r, psnr_g, psnr_b)
    else:
        sse = sum((v1 - v2) ** 2 for v1, v2 in zip(pixels1, pixels2))
        if sse == 0:
            return float('inf')
        max_f = max(pixels1)
        return 10 * math.log10((MN * (max_f ** 2)) / sse)


def doMD(pixels1, pixels2):
    if len(pixels1) != len(pixels2):
        raise ValueError("Images must have the exact same dimensions for comparison.")

    if isinstance(pixels1[0], tuple):
        md_r = max(abs(p1[0] - p2[0]) for p1, p2 in zip(pixels1, pixels2))
        md_g = max(abs(p1[1] - p2[1]) for p1, p2 in zip(pixels1, pixels2))
        md_b = max(abs(p1[2] - p2[2]) for p1, p2 in zip(pixels1, pixels2))
        return (md_r, md_g, md_b)
    else:
        return max(abs(v1 - v2) for v1, v2 in zip(pixels1, pixels2))


def doHistogram(pixels):
    hist_w = 256
    hist_h = 200
    is_rgb = isinstance(pixels[0], tuple)

    if is_rgb:
        # Initialise white background
        result = [(255, 255, 255)] * (hist_w * hist_h)
        hist_r, hist_g, hist_b = [0] * 256, [0] * 256, [0] * 256

        for p in pixels:
            hist_r[p[0]] += 1
            hist_g[p[1]] += 1
            hist_b[p[2]] += 1

        max_val = max(max(hist_r), max(hist_g), max(hist_b))
        if max_val == 0: max_val = 1

        for x in range(256):
            r_bar = int((hist_r[x] / max_val) * hist_h)
            g_bar = int((hist_g[x] / max_val) * hist_h)
            b_bar = int((hist_b[x] / max_val) * hist_h)

            # Render RGB lines
            for y in range(hist_h):
                r_col = 255 if (hist_h - y) > r_bar else 0
                g_col = 255 if (hist_h - y) > g_bar else 0
                b_col = 255 if (hist_h - y) > b_bar else 0
                result[y * hist_w + x] = (r_col, g_col, b_col)
    else:
        # Grayscale histogram
        result = [255] * (hist_w * hist_h)
        hist = [0] * 256

        for p in pixels:
            hist[p] += 1

        max_val = max(hist)
        if max_val == 0: max_val = 1

        for x in range(256):
            bar_h = int((hist[x] / max_val) * hist_h)
            for y in range(hist_h - bar_h, hist_h):
                result[y * hist_w + x] = 0

    return result, hist_w, hist_h



def doHexponent(pixels, param):

    alpha = float(param)
    if alpha == 0:
        raise ValueError("Alpha cannot be zero.")

    g_min = 0  # Defaulting minimum output brightness to 0
    N = len(pixels)
    is_rgb = isinstance(pixels[0], tuple)
    result = []

    def calculate_lut(hist):
        # Calculate Cumulative Distribution Function (CDF)
        cdf = [0] * 256
        cdf[0] = hist[0]
        for i in range(1, 256):
            cdf[i] = cdf[i - 1] + hist[i]

        lut = [0] * 256
        for i in range(256):
            cdf_val = cdf[i]
            # Prevent math domain error for log(0) when CDF equals total pixels
            if cdf_val == N:
                cdf_val = N - 1
            try:
                # Apply the exponential equation
                val = g_min - (1.0 / alpha) * math.log(1.0 - (cdf_val / float(N)))
                lut[i] = max(0, min(255, int(val)))
            except ValueError:
                lut[i] = 255
        return lut

    if is_rgb:
        # Separate channels for RGB
        hist_r, hist_g, hist_b = [0] * 256, [0] * 256, [0] * 256
        for p in pixels:
            hist_r[p[0]] += 1
            hist_g[p[1]] += 1
            hist_b[p[2]] += 1

        lut_r = calculate_lut(hist_r)
        lut_g = calculate_lut(hist_g)
        lut_b = calculate_lut(hist_b)

        for p in pixels:
            result.append((lut_r[p[0]], lut_g[p[1]], lut_b[p[2]]))
    else:
        # Grayscale
        hist = [0] * 256
        for p in pixels:
            hist[p] += 1

        lut = calculate_lut(hist)
        for p in pixels:
            result.append(lut[p])

    return result


# (C1) Mean
def doCMean(pixels):
    N = len(pixels)
    is_rgb = isinstance(pixels[0], tuple)
    if is_rgb:
        hr, hg, hb = [0] * 256, [0] * 256, [0] * 256
        for p in pixels:
            hr[p[0]] += 1
            hg[p[1]] += 1
            hb[p[2]] += 1
        mean_r = sum(m * hr[m] for m in range(256)) / N
        mean_g = sum(m * hg[m] for m in range(256)) / N
        mean_b = sum(m * hb[m] for m in range(256)) / N
        return (mean_r, mean_g, mean_b)
    else:
        h = [0] * 256
        for p in pixels:
            h[p] += 1
        mean = sum(m * h[m] for m in range(256)) / N
        return mean


# (C1) Variance
def doCVariance(pixels):
    N = len(pixels)
    is_rgb = isinstance(pixels[0], tuple)
    if is_rgb:
        hr, hg, hb = [0] * 256, [0] * 256, [0] * 256
        for p in pixels:
            hr[p[0]] += 1
            hg[p[1]] += 1
            hb[p[2]] += 1
        mean_r = sum(m * hr[m] for m in range(256)) / N
        mean_g = sum(m * hg[m] for m in range(256)) / N
        mean_b = sum(m * hb[m] for m in range(256)) / N
        var_r = sum(((m - mean_r) ** 2) * hr[m] for m in range(256)) / N
        var_g = sum(((m - mean_g) ** 2) * hg[m] for m in range(256)) / N
        var_b = sum(((m - mean_b) ** 2) * hb[m] for m in range(256)) / N
        return (var_r, var_g, var_b)
    else:
        h = [0] * 256
        for p in pixels:
            h[p] += 1
        mean = sum(m * h[m] for m in range(256)) / N
        var = sum(((m - mean) ** 2) * h[m] for m in range(256)) / N
        return var


# (C2) Standard Deviation
def doCStdev(pixels):
    N = len(pixels)
    is_rgb = isinstance(pixels[0], tuple)
    if is_rgb:
        hr, hg, hb = [0] * 256, [0] * 256, [0] * 256
        for p in pixels:
            hr[p[0]] += 1
            hg[p[1]] += 1
            hb[p[2]] += 1
        mean_r = sum(m * hr[m] for m in range(256)) / N
        mean_g = sum(m * hg[m] for m in range(256)) / N
        mean_b = sum(m * hb[m] for m in range(256)) / N
        var_r = sum(((m - mean_r) ** 2) * hr[m] for m in range(256)) / N
        var_g = sum(((m - mean_g) ** 2) * hg[m] for m in range(256)) / N
        var_b = sum(((m - mean_b) ** 2) * hb[m] for m in range(256)) / N
        return (math.sqrt(var_r), math.sqrt(var_g), math.sqrt(var_b))
    else:
        h = [0] * 256
        for p in pixels:
            h[p] += 1
        mean = sum(m * h[m] for m in range(256)) / N
        var = sum(((m - mean) ** 2) * h[m] for m in range(256)) / N
        return math.sqrt(var)


# (C2) Variation Coefficient I
def doCVarCoI(pixels):
    N = len(pixels)
    is_rgb = isinstance(pixels[0], tuple)
    if is_rgb:
        hr, hg, hb = [0] * 256, [0] * 256, [0] * 256
        for p in pixels:
            hr[p[0]] += 1
            hg[p[1]] += 1
            hb[p[2]] += 1
        mean_r = sum(m * hr[m] for m in range(256)) / N
        mean_g = sum(m * hg[m] for m in range(256)) / N
        mean_b = sum(m * hb[m] for m in range(256)) / N
        var_r = sum(((m - mean_r) ** 2) * hr[m] for m in range(256)) / N
        var_g = sum(((m - mean_g) ** 2) * hg[m] for m in range(256)) / N
        var_b = sum(((m - mean_b) ** 2) * hb[m] for m in range(256)) / N
        vc_r = math.sqrt(var_r) / mean_r if mean_r != 0 else float('inf')
        vc_g = math.sqrt(var_g) / mean_g if mean_g != 0 else float('inf')
        vc_b = math.sqrt(var_b) / mean_b if mean_b != 0 else float('inf')
        return (vc_r, vc_g, vc_b)
    else:
        h = [0] * 256
        for p in pixels:
            h[p] += 1
        mean = sum(m * h[m] for m in range(256)) / N
        var = sum(((m - mean) ** 2) * h[m] for m in range(256)) / N
        return math.sqrt(var) / mean if mean != 0 else float('inf')


# (C3) Asymmetry Coefficient
def doCAsyCo(pixels):
    N = len(pixels)
    is_rgb = isinstance(pixels[0], tuple)
    if is_rgb:
        hr, hg, hb = [0] * 256, [0] * 256, [0] * 256
        for p in pixels:
            hr[p[0]] += 1
            hg[p[1]] += 1
            hb[p[2]] += 1
        mean_r = sum(m * hr[m] for m in range(256)) / N
        mean_g = sum(m * hg[m] for m in range(256)) / N
        mean_b = sum(m * hb[m] for m in range(256)) / N
        var_r = sum(((m - mean_r) ** 2) * hr[m] for m in range(256)) / N
        var_g = sum(((m - mean_g) ** 2) * hg[m] for m in range(256)) / N
        var_b = sum(((m - mean_b) ** 2) * hb[m] for m in range(256)) / N
        std_r, std_g, std_b = math.sqrt(var_r), math.sqrt(var_g), math.sqrt(var_b)

        asy_r = (1 / (std_r ** 3)) * (
                    sum(((m - mean_r) ** 3) * hr[m] for m in range(256)) / N) if std_r != 0 else float('inf')
        asy_g = (1 / (std_g ** 3)) * (
                    sum(((m - mean_g) ** 3) * hg[m] for m in range(256)) / N) if std_g != 0 else float('inf')
        asy_b = (1 / (std_b ** 3)) * (
                    sum(((m - mean_b) ** 3) * hb[m] for m in range(256)) / N) if std_b != 0 else float('inf')
        return (asy_r, asy_g, asy_b)
    else:
        h = [0] * 256
        for p in pixels:
            h[p] += 1
        mean = sum(m * h[m] for m in range(256)) / N
        var = sum(((m - mean) ** 2) * h[m] for m in range(256)) / N
        std = math.sqrt(var)
        if std == 0: return float('inf')
        return (1 / (std ** 3)) * (sum(((m - mean) ** 3) * h[m] for m in range(256)) / N)


# (C4) Flattening Coefficient
def doCFlaCo(pixels):
    N = len(pixels)
    is_rgb = isinstance(pixels[0], tuple)
    if is_rgb:
        hr, hg, hb = [0] * 256, [0] * 256, [0] * 256
        for p in pixels:
            hr[p[0]] += 1
            hg[p[1]] += 1
            hb[p[2]] += 1
        mean_r = sum(m * hr[m] for m in range(256)) / N
        mean_g = sum(m * hg[m] for m in range(256)) / N
        mean_b = sum(m * hb[m] for m in range(256)) / N
        var_r = sum(((m - mean_r) ** 2) * hr[m] for m in range(256)) / N
        var_g = sum(((m - mean_g) ** 2) * hg[m] for m in range(256)) / N
        var_b = sum(((m - mean_b) ** 2) * hb[m] for m in range(256)) / N
        std_r, std_g, std_b = math.sqrt(var_r), math.sqrt(var_g), math.sqrt(var_b)

        fla_r = (1 / (std_r ** 4)) * (
                    sum(((m - mean_r) ** 4) * hr[m] for m in range(256)) / N) - 3 if std_r != 0 else float('inf')
        fla_g = (1 / (std_g ** 4)) * (
                    sum(((m - mean_g) ** 4) * hg[m] for m in range(256)) / N) - 3 if std_g != 0 else float('inf')
        fla_b = (1 / (std_b ** 4)) * (
                    sum(((m - mean_b) ** 4) * hb[m] for m in range(256)) / N) - 3 if std_b != 0 else float('inf')
        return (fla_r, fla_g, fla_b)
    else:
        h = [0] * 256
        for p in pixels:
            h[p] += 1
        mean = sum(m * h[m] for m in range(256)) / N
        var = sum(((m - mean) ** 2) * h[m] for m in range(256)) / N
        std = math.sqrt(var)
        if std == 0: return float('inf')
        return (1 / (std ** 4)) * (sum(((m - mean) ** 4) * h[m] for m in range(256)) / N) - 3


# (C5) Variation Coefficient II
def doCVarCoII(pixels):
    N = len(pixels)
    is_rgb = isinstance(pixels[0], tuple)
    if is_rgb:
        hr, hg, hb = [0] * 256, [0] * 256, [0] * 256
        for p in pixels:
            hr[p[0]] += 1
            hg[p[1]] += 1
            hb[p[2]] += 1
        vc2_r = (1 / (N ** 2)) * sum(h ** 2 for h in hr)
        vc2_g = (1 / (N ** 2)) * sum(h ** 2 for h in hg)
        vc2_b = (1 / (N ** 2)) * sum(h ** 2 for h in hb)
        return (vc2_r, vc2_g, vc2_b)
    else:
        h = [0] * 256
        for p in pixels:
            h[p] += 1
        return (1 / (N ** 2)) * sum(val ** 2 for val in h)


# (C6) Information Source Entropy
def doCEntropy(pixels):
    N = len(pixels)
    is_rgb = isinstance(pixels[0], tuple)
    if is_rgb:
        hr, hg, hb = [0] * 256, [0] * 256, [0] * 256
        for p in pixels:
            hr[p[0]] += 1
            hg[p[1]] += 1
            hb[p[2]] += 1

        ent_r, ent_g, ent_b = 0, 0, 0
        for val in hr:
            if val > 0: ent_r -= (val / N) * math.log2(val / N)
        for val in hg:
            if val > 0: ent_g -= (val / N) * math.log2(val / N)
        for val in hb:
            if val > 0: ent_b -= (val / N) * math.log2(val / N)
        return (ent_r, ent_g, ent_b)
    else:
        h = [0] * 256
        for p in pixels:
            h[p] += 1
        entropy = 0
        for val in h:
            if val > 0:
                p = val / N
                entropy -= p * math.log2(p)
        return entropy



# UNIVERSAL CONVOLUTION (Theoretical implementation)
# Required by the assignment guidelines to prove the understanding of the generic algorithm.
# This function works with ANY 3x3 mask by iterating over a 3x3 neighborhood for every pixel.
def doConvolutionUniversal(pixels, width, height, mask):
    result = []
    is_rgb = isinstance(pixels[0], tuple)
    
    for y in range(height):
        for x in range(width):
            if is_rgb:
                sum_r, sum_g, sum_b = 0, 0, 0
                # Double loop to iterate through the 3x3 neighborhood
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        # Clamping (max/min) prevents index errors at the image borders
                        cy = max(0, min(height - 1, y + dy))
                        cx = max(0, min(width - 1, x + dx))
                        weight = mask[dy+1][dx+1]
                        
                        p = pixels[cy * width + cx]
                        # Multiply pixel intensity by the mask weight and accumulate
                        sum_r += p[0] * weight
                        sum_g += p[1] * weight
                        sum_b += p[2] * weight
                # Clip the final sum to ensure values stay within valid RGB range [0, 255]
                result.append((max(0, min(255, int(sum_r))), max(0, min(255, int(sum_g))), max(0, min(255, int(sum_b)))))
            else:
                sum_v = 0
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        cy = max(0, min(height - 1, y + dy))
                        cx = max(0, min(width - 1, x + dx))
                        weight = mask[dy+1][dx+1]
                        
                        sum_v += pixels[cy * width + cx] * weight
                result.append(max(0, min(255, int(sum_v))))
    return result

def doLaplaceOptimized(pixels, width, height):
    result = []
    is_rgb = isinstance(pixels[0], tuple)
    
    for y in range(height):
        y_up = max(0, y - 1) * width
        y_down = min(height - 1, y + 1) * width
        y_cen = y * width
        
        for x in range(width):
            x_left = max(0, x - 1)
            x_right = min(width - 1, x + 1)
            x_cen = x
            
            if is_rgb:
                # Fetch the 5 necessary pixels (Center and its direct cross neighbors)
                c = pixels[y_cen + x_cen]
                u = pixels[y_up + x_cen]
                d = pixels[y_down + x_cen]
                l = pixels[y_cen + x_left]
                r = pixels[y_cen + x_right]
                
                # Apply the specific S5 formula directly
                r_val = 4 * c[0] - u[0] - d[0] - l[0] - r[0]
                g_val = 4 * c[1] - u[1] - d[1] - l[1] - r[1]
                b_val = 4 * c[2] - u[2] - d[2] - l[2] - r[2]
                
                # Clip the result
                result.append((max(0, min(255, r_val)), max(0, min(255, g_val)), max(0, min(255, b_val))))
            else:
                c = pixels[y_cen + x_cen]
                u = pixels[y_up + x_cen]
                d = pixels[y_down + x_cen]
                l = pixels[y_cen + x_left]
                r = pixels[y_cen + x_right]
                
                v = 4 * c - u - d - l - r
                result.append(max(0, min(255, v)))
                
    return result

def doRobertsII(pixels, width, height):
    result = []
    is_rgb = isinstance(pixels[0], tuple)
    
    for y in range(height):
        for x in range(width):
            # Clamping to avoid index out of bounds when looking at the right and bottom edges
            x_curr = x
            y_curr = y
            x_next = min(width - 1, x + 1)
            y_next = min(height - 1, y + 1)
            
            if is_rgb:
                # Fetch the 4 pixels forming the 2x2 block
                p00 = pixels[y_curr * width + x_curr] # Top-Left: x(n,m)
                p11 = pixels[y_next * width + x_next] # Bottom-Right: x(n+1,m+1)
                p10 = pixels[y_curr * width + x_next] # Top-Right: x(n+1,m)
                p01 = pixels[y_next * width + x_curr] # Bottom-Left: x(n,m+1)
                
                # Calculate the absolute difference of the diagonals
                r_val = abs(p00[0] - p11[0]) + abs(p10[0] - p01[0])
                g_val = abs(p00[1] - p11[1]) + abs(p10[1] - p01[1])
                b_val = abs(p00[2] - p11[2]) + abs(p10[2] - p01[2])
                
                result.append((max(0, min(255, r_val)), max(0, min(255, g_val)), max(0, min(255, b_val))))
            else:
                p00 = pixels[y_curr * width + x_curr]
                p11 = pixels[y_next * width + x_next]
                p10 = pixels[y_curr * width + x_next]
                p01 = pixels[y_next * width + x_curr]
                
                v = abs(p00 - p11) + abs(p10 - p01)
                result.append(max(0, min(255, v)))
                
    return result

def printHelp():
    print("""
Image Processing Application

Usage:
    python myWonderfulImProcApp.py --brightness VALUE images_input\input.bmp images_output\output.bmp
    python myWonderfulImProcApp.py --contrast VALUE images_input\input.bmp images_output\output.bmp
    python myWonderfulImProcApp.py --negative images_input\input.bmp images_output\output.bmp
    python myWonderfulImProcApp.py --hflip images_input\input.bmp images_output\output.bmp
    python myWonderfulImProcApp.py --vflip images_input\input.bmp images_output\output.bmp
    python myWonderfulImProcApp.py --dflip images_input\input.bmp images_output\output.bmp
    python myWonderfulImProcApp.py --shrink VALUE images_input\input.bmp images_output\output.bmp
    python myWonderfulImProcApp.py --enlarge VALUE images_input\input.bmp images_output\output.bmp
    python myWonderfulImProcApp.py --min WINDOW_SIZE images_input\input.bmp images_output\output.bmp
    python myWonderfulImProcApp.py --max WINDOW_SIZE images_input\input.bmp images_output\output.bmp
    python myWonderfulImProcApp.py --adaptive SMAX images_input\input.bmp images_output\output.bmp
    python myWonderfulImProcApp.py --mse images_input\original.bmp images_input\compared.bmp
    python myWonderfulImProcApp.py --pmse images_input\original.bmp images_input\compared.bmp
    python myWonderfulImProcApp.py --snr images_input\original.bmp images_input\compared.bmp
    python myWonderfulImProcApp.py --psnr images_input\original.bmp images_input\compared.bmp
    python myWonderfulImProcApp.py --md images_input\original.bmp images_input\compared.bmp
    python myWonderfulImProcApp.py --histogram images_input\input.bmp images_output\output.bmp
    python myWonderfulImProcApp.py --hexponent VALUE images_input\input.bmp images_output\output.bmp
    python myWonderfulImProcApp.py --cmean images_input\input.bmp
    python myWonderfulImProcApp.py --cvariance images_input\input.bmp
    python myWonderfulImProcApp.py --cstdev images_input\input.bmp
    python myWonderfulImProcApp.py --cvarcoi images_input\input.bmp
    python myWonderfulImProcApp.py --casyco images_input\input.bmp
    python myWonderfulImProcApp.py --cflaco images_input\input.bmp
    python myWonderfulImProcApp.py --cvarcoii images_input\input.bmp
    python myWonderfulImProcApp.py --centropy images_input\input.bmp
    python myWonderfulImProcApp.py --slaplace images_input\input.bmp images_output\output.bmp
    python myWonderfulImProcApp.py --orobertsii images_input\input.bmp images_output\output.bmp

    
Commands:
    --brightness VALUE  : Modify brightness by adding VALUE to each pixel channel.
    --contrast VALUE    : Modify contrast using a linear factor.
    --negative          : Invert each pixel channel.
    --hflip             : Flip the image horizontally.
    --vflip             : Flip the image vertically.
    --dflip             : Flip the image diagonally.
    --shrink VALUE      : Shrink the image by an integer factor.
    --enlarge VALUE     : Enlarge the image by an integer factor.
    --min WINDOW_SIZE   : Apply Minimum filter (odd window size).
    --max WINDOW_SIZE   : Apply Maximum filter (odd window size).
    --adaptive SMAX     : Apply Adaptive Median filter (odd max window size).
    --mse               : Mean square error
    --pmse              : Peak mean square error
    --snr               : Signal to noise ratio [dB]
    --psnr              : Peak signal to noise ratio [dB]
    --md                : Maximum difference
    --histogram         : Generate and save a 256x200 image of the histogram.
    --hexponent VALUE   : Apply Exponential final probability density function.
    --cmean             : Image characteristic: Mean
    --cvariance         : Image characteristic: Variance
    --cstdev            : Image characteristic: Standard deviation
    --cvarcoi           : Image characteristic: Variation coefficient I
    --casyco            : Image characteristic: Asymmetry coefficient
    --cflaco            : Image characteristic: Flattening coefficient
    --cvarcoii          : Image characteristic: Variation coefficient II
    --centropy          : Image characteristic: Information source entropy
    --slaplace          : Extract details using Laplacian linear filter.
    --orobertsii        : Non-linear filtration using Roberts operator II.
    
    --help              : Display this help message.
""")

###########################
# HERE THE MAIN PART STARTS
###########################

def main():

    if len(sys.argv) == 1:
        print("No command line parameters given.")
        print("Use --help for available commands.")
        return

    if sys.argv[1] == "--help":
        printHelp()
        return

    command = sys.argv[1]
    
    # Define groups of commands
    metric_commands = ("--mse", "--pmse", "--snr", "--psnr", "--md")
    char_commands = (
        "--cmean", "--cvariance", "--cstdev", "--cvarcoi",
        "--casyco", "--cflaco", "--cvarcoii", "--centropy"
    )

    # Operations requiring an additional parameter (Value, Factor, Window Size)
    if command in ("--brightness", "--contrast", "--shrink", "--enlarge", "--min", "--max", "--adaptive", "--hexponent"):
        if len(sys.argv) != 5:
            print("Usage: command VALUE input.bmp output.bmp")
            return
        param = sys.argv[2]
        input_file = sys.argv[3]
        output_file = sys.argv[4]

    # Operations that do not require an additional parameter
    elif command in ("--negative", "--hflip", "--vflip", "--dflip", "--slaplace", "--histogram", "--orobertsii"):
        if len(sys.argv) != 4:
            print(f"Usage: {command} input.bmp output.bmp")
            return
        param = None
        input_file = sys.argv[2]
        output_file = sys.argv[3]
        
    # Metrics computations requiring two input files instead of parameter + output
    elif command in metric_commands:
        if len(sys.argv) != 4:
            print(f"Usage: {command} original_image.bmp compared_image.bmp")
            return
        param = None
        input_file = sys.argv[2]
        output_file = sys.argv[3] # Represents the compared image here
        # Nowy blok - operacje wymagające tylko jednego pliku (bez pliku wyjściowego)
    elif command in char_commands:
        if len(sys.argv) != 3:
            print(f"Usage: {command} input.bmp")
            return
        param = None
        input_file = sys.argv[2]
        output_file = None
    else:
        print("Unknown command:", command)
        print("Use --help for available commands.")
        return


    try:
        # Open the first image
        with Image.open(input_file) as image:
            mode = "L" if image.mode == "L" else "RGB"
            image = image.convert(mode)
            width, height = image.size
            pixels = list(image.getdata())

        # Process metrics (2 images comparison)
        if command in metric_commands:
            with Image.open(output_file) as image2:
                image2 = image2.convert(mode)
                if image2.size != (width, height):
                    raise ValueError("Images must have the same dimensions for comparison.")
                pixels2 = list(image2.getdata())
                
            if command == "--mse":
                result = doMSE(pixels, pixels2)
            elif command == "--pmse":
                result = doPMSE(pixels, pixels2)
            elif command == "--snr":
                result = doSNR(pixels, pixels2)
            elif command == "--psnr":
                result = doPSNR(pixels, pixels2)
            elif command == "--md":
                result = doMD(pixels, pixels2)
                
            print(f"[{command.upper()}] Result: {result}")
            return
        if command in char_commands:
            if command == "--cmean":
                result = doCMean(pixels)
            elif command == "--cvariance":
                result = doCVariance(pixels)
            elif command == "--cstdev":
                result = doCStdev(pixels)
            elif command == "--cvarcoi":
                result = doCVarCoI(pixels)
            elif command == "--casyco":
                result = doCAsyCo(pixels)
            elif command == "--cflaco":
                result = doCFlaCo(pixels)
            elif command == "--cvarcoii":
                result = doCVarCoII(pixels)
            elif command == "--centropy":
                result = doCEntropy(pixels)

            if isinstance(result, tuple):
                print(f"[{command.upper()}] Result (R, G, B): ({result[0]:.4f}, {result[1]:.4f}, {result[2]:.4f})")
            else:
                print(f"[{command.upper()}] Result: {result:.4f}")
            return
        # Process standard image transformations
        if command == "--brightness":
            pixels = doBrightness(pixels, param)
        elif command == "--contrast":
            pixels = doContrast(pixels, param)
        elif command == "--negative":
            pixels = doNegative(pixels)
        elif command == "--hflip":
            pixels = doHflip(pixels, width, height)
        elif command == "--vflip":
            pixels = doVflip(pixels, width, height)
        elif command == "--dflip":
            pixels = doDflip(pixels, width, height)
        elif command == "--shrink":
            pixels, width, height = doShrink(pixels, width, height, param)
        elif command == "--enlarge":
            pixels, width, height = doEnlarge(pixels, width, height, param)
        elif command == "--min":
            pixels = doMin(pixels, width, height, param)
        elif command == "--max":
            pixels = doMax(pixels, width, height, param)
        elif command == "--adaptive":
            pixels = doAdaptive(pixels, width, height, param)
        elif command == "--hexponent":
            pixels = doHexponent(pixels, param)
        elif command == "--histogram":
            pixels, width, height = doHistogram(pixels)
        elif command == "--slaplace":
            pixels = doLaplaceOptimized(pixels, width, height)
        elif command == "--orobertsii":
            pixels = doRobertsII(pixels, width, height)

        # Create new image and save
        result_img = Image.new(mode, (width, height))
        result_img.putdata(pixels)
        result_img.save(output_file, format="BMP")

        print("Processing completed successfully.")
        print("Output saved to:", output_file)

    except (OSError, ValueError) as error:
        print("Error:", error)

if __name__ == "__main__":
    main()