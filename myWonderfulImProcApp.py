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
    # By iterating over x first, we transpose the image
    for x in range(width):
        for y in range(height):
            old_index = (y * width) + x
            result.append(pixels[old_index])
    return result

def doShrink(pixels, width, height, param):
    factor = int(param)
    if factor <= 0:
        raise ValueError("Shrink factor must be greater than 0!")
    result = []
    new_width = width // factor
    new_height = height // factor
    
    # Nearest neighbor interpolation: we skip pixels based on the factor
    for y in range(new_height):
        for x in range(new_width):
            old_index = (y * factor * width) + (x * factor)
            result.append(pixels[old_index])
    return result, new_width, new_height

def doEnlarge(pixels, width, height, param):
    factor = int(param)
    if factor <= 0:
        raise ValueError("Enlarge factor must be greater than 0!")
    result = []
    new_width = width * factor
    new_height = height * factor
    
    # Nearest neighbor interpolation: we duplicate pixels to fill the new space
    for y in range(new_height):
        old_y = y // factor
        for x in range(new_width):
            old_x = x // factor
            old_index = (old_y * width) + old_x
            result.append(pixels[old_index])
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
    # Flatten pixels if they are RGB tuples
    if isinstance(pixels1[0], tuple):
        vals1 = [c for p in pixels1 for c in p] # Example: [(R1,G1,B1), (R2,G2,B2)] -> [R1,G1,B1,R2,G2,B2]
        vals2 = [c for p in pixels2 for c in p]
    else:
        vals1 = pixels1
        vals2 = pixels2
        
    if len(vals1) != len(vals2):
        raise ValueError("Images must have the exact same dimensions for comparison.")
        
    MN = len(vals1)
    sse = sum((v1 - v2) ** 2 for v1, v2 in zip(vals1, vals2)) # Example: sum((R1-R2)^2 + (G1-G2)^2 + (B1-B2)^2 + ...)
    
    return sse / MN

def doPMSE(pixels1, pixels2):
    if isinstance(pixels1[0], tuple):
        vals1 = [c for p in pixels1 for c in p]
        vals2 = [c for p in pixels2 for c in p]
    else:
        vals1 = pixels1
        vals2 = pixels2
        
    if len(vals1) != len(vals2):
        raise ValueError("Images must have the exact same dimensions for comparison.")
        
    MN = len(vals1)
    sse = sum((v1 - v2) ** 2 for v1, v2 in zip(vals1, vals2))
    max_f = max(vals1)
    
    # Guard against division by zero if the image is completely black
    if max_f == 0:
        return float('inf')
        
    mse = sse / MN
    pmse = mse / (max_f ** 2)
    return pmse

def doSNR(pixels1, pixels2):
    if isinstance(pixels1[0], tuple):
        vals1 = [c for p in pixels1 for c in p]
        vals2 = [c for p in pixels2 for c in p]
    else:
        vals1 = pixels1
        vals2 = pixels2
        
    if len(vals1) != len(vals2):
        raise ValueError("Images must have the exact same dimensions for comparison.")
        
    sse = sum((v1 - v2) ** 2 for v1, v2 in zip(vals1, vals2))
    
    # Guard against division by zero if both images are perfectly identical
    if sse == 0:
        return float('inf')
        
    sum_sq_f = sum(v ** 2 for v in vals1)
    snr = 10 * math.log10(sum_sq_f / sse)
    return snr

def doPSNR(pixels1, pixels2):
    if isinstance(pixels1[0], tuple):
        vals1 = [c for p in pixels1 for c in p]
        vals2 = [c for p in pixels2 for c in p]
    else:
        vals1 = pixels1
        vals2 = pixels2
        
    if len(vals1) != len(vals2):
        raise ValueError("Images must have the exact same dimensions for comparison.")
        
    MN = len(vals1)
    sse = sum((v1 - v2) ** 2 for v1, v2 in zip(vals1, vals2))
    
    # Guard against division by zero
    if sse == 0:
        return float('inf')
        
    max_f = max(vals1)
    sum_max_sq = MN * (max_f ** 2)
    psnr = 10 * math.log10(sum_max_sq / sse)
    return psnr

def doMD(pixels1, pixels2):
    if isinstance(pixels1[0], tuple):
        vals1 = [c for p in pixels1 for c in p]
        vals2 = [c for p in pixels2 for c in p]
    else:
        vals1 = pixels1
        vals2 = pixels2
        
    if len(vals1) != len(vals2):
        raise ValueError("Images must have the exact same dimensions for comparison.")
        
    md = max(abs(v1 - v2) for v1, v2 in zip(vals1, vals2))
    return md


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

    # Operations requiring an additional parameter (Value, Factor, Window Size)
    if command in ("--brightness", "--contrast", "--shrink", "--enlarge", "--min", "--max", "--adaptive"):
        if len(sys.argv) != 5:
            print("Usage: command VALUE input.bmp output.bmp")
            return
        param = sys.argv[2]
        input_file = sys.argv[3]
        output_file = sys.argv[4]

    # Operations that do not require an additional parameter
    elif command in ("--negative", "--hflip", "--vflip", "--dflip"):
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