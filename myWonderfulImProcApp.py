import sys
from PIL import Image

######################
# FUNCTION DEFINITIONS
######################

def doBrightness(pixels, param):
    # convert the brightness parameter to a number
    value = float(param)
    result = []

    # process each pixel in the image
    for pixel in pixels:

        # if the pixel is RGB, process each color channel separately
        if isinstance(pixel, tuple):
            new_pixel = tuple(
                max(0, min(255, int(channel + value)))
                for channel in pixel
            )

        # if the pixel is grayscale, process its single value
        else:
            new_pixel = max(0, min(255, int(pixel + value)))

        # add the modified pixel to the result list
        result.append(new_pixel)

    # return the list of modified pixels
    return result


def doContrast(pixels, param):
    # convert the contrast parameter to a number
    factor = float(param)
    result = []

    # check that the contrast factor is not negative
    if factor < 0:
        raise ValueError("Contrast factor cannot be negative !")

    # process each pixel in the image
    for pixel in pixels:

        # if the pixel is RGB, apply the contrast formula to each channel
        if isinstance(pixel, tuple):
            new_pixel = tuple(
                max(0, min(255, int((channel - 128) * factor + 128)))
                for channel in pixel
            )

        # if the pixel is grayscale, apply the formula to its value
        else:
            new_pixel = max(
                0, min(255, int((pixel - 128) * factor + 128))
            )

        # add the modified pixel to the result list
        result.append(new_pixel)

    # return the list of modified pixels
    return result


def doNegative(pixels):
    result = []

    # process each pixel in the image
    for pixel in pixels:

        # if the pixel is RGB, invert each color channel
        if isinstance(pixel, tuple):
            new_pixel = tuple(255 - channel for channel in pixel)

        # if the pixel is grayscale, invert its value
        else:
            new_pixel = 255 - pixel

        # add the inverted pixel to the result list
        result.append(new_pixel)

    # return the list of modified pixels
    return result


def doHflip(pixels, width, height):
    result = []

    # process the image row by row
    for y in range(height):
        # find the index of the last pixel in the current row
        row_end_index = (y * width) + width - 1

        # loop backwards through the current row
        for x in range(width):
            # subtract x from the end index to walk backwards
            pixel = pixels[row_end_index - x]
            result.append(pixel)

    # return the list of horizontally flipped pixels
    return result


def doVflip(pixels, width, height):
    result = []

    # process the image row by row
    for y in range(height):
        # calculate the y-coordinate of the corresponding row from the bottom
        bottom_y = (height - 1) - y

        # find the starting index of that bottom row
        row_start_index = bottom_y * width

        # loop forwards through the current row
        for x in range(width):
            # grab the pixel moving left to right
            pixel = pixels[row_start_index + x]
            result.append(pixel)

    # return the list of vertically flipped pixels
    return result

def doDflip(pixels, width, height):
    result = []

   #combination of H and V flips
    for x in range(width):
        for y in range(height):
            # calculate the index of the pixel in the original image
            old_index = (y * width) + x
            result.append(pixels[old_index])

    # return the list of diagonally flipped pixels
    return result


def doShrink(pixels, width, height, param):
    # convert the shrink factor to an integer
    factor = int(param)

    # check that the shrink factor is valid
    if factor <= 0:
        raise ValueError("Shrink factor must be greater than 0!")

    result = []

    # calculate new dimensions after shrinking
    new_width = width // factor
    new_height = height // factor

    # process the image by sampling pixels based on the factor
    for y in range(new_height):
        for x in range(new_width):
            # calculate the index of the pixel in the original image
            old_index = (y * factor * width) + (x * factor)
            result.append(pixels[old_index])

    # return the shrunk pixels and the new dimensions
    return result, new_width, new_height


def doEnlarge(pixels, width, height, param):
    # convert the enlarge factor to an integer
    factor = int(param)

    # check that the enlarge factor is valid
    if factor <= 0:
        raise ValueError("Enlarge factor must be greater than 0!")

    result = []

    # calculate new dimensions after enlarging
    new_width = width * factor
    new_height = height * factor

    # process the new image row by row, column by column
    for y in range(new_height):
        # map current row to the original row
        old_y = y // factor
        for x in range(new_width):
            # map current column to the original column
            old_x = x // factor

            # calculate the index of the pixel in the original image
            old_index = (old_y * width) + old_x
            result.append(pixels[old_index])

    # return the enlarged pixels and the new dimensions
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
            
            # extract the local window, clamping coordinates to the image boundaries
            for wy in range(y - offset, y + offset + 1):
                cy = max(0, min(height - 1, wy))
                for wx in range(x - offset, x + offset + 1):
                    cx = max(0, min(width - 1, wx))
                    window.append(pixels[cy * width + cx])
            
            if is_rgb:
                # calculate minimum for each channel independently
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
            
            # extract the local window, clamping coordinates to the image boundaries
            for wy in range(y - offset, y + offset + 1):
                cy = max(0, min(height - 1, wy))
                for wx in range(x - offset, x + offset + 1):
                    cx = max(0, min(width - 1, wx))
                    window.append(pixels[cy * width + cx])
            
            if is_rgb:
                # calculate maximum for each channel independently
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
    
    def adaptive_process(x, y, channel_idx=None):
        window_size = 3
        
        while window_size <= s_max:
            offset = window_size // 2
            window = []
            
            # extract the local window for the current channel, clamping coordinates
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
            
            # Stage A
            A1 = z_med - z_min
            A2 = z_med - z_max
            
            if A1 > 0 and A2 < 0:
                # Stage B
                B1 = z_xy - z_min
                B2 = z_xy - z_max
                if B1 > 0 and B2 < 0:
                    return z_xy
                else:
                    return z_med
            else:
                # increase window size
                window_size += 2
                
        # if maximum window size is reached then return z_xy
        pixel_val = pixels[y * width + x]
        return pixel_val[channel_idx] if channel_idx is not None else pixel_val

    for y in range(height):
        for x in range(width):
            if is_rgb:
                new_pixel = (
                    adaptive_process(x, y, 0), # Red
                    adaptive_process(x, y, 1), # Green
                    adaptive_process(x, y, 2)  # Blue
                )
                result.append(new_pixel)
            else:
                result.append(adaptive_process(x, y, None))
                
    return result

def printHelp():
    # display the available commands and their usage
    print("""
Image Processing Application

Usage:
    python myWonderfulImProcApp.py --brightness VALUE input.bmp output.bmp
    python myWonderfulImProcApp.py --contrast VALUE input.bmp output.bmp
    python myWonderfulImProcApp.py --negative input.bmp output.bmp
    python myWonderfulImProcApp.py --hflip input.bmp output.bmp
    python myWonderfulImProcApp.py --vflip input.bmp output.bmp
    python myWonderfulImProcApp.py --shrink VALUE input.bmp output.bmp
    python myWonderfulImProcApp.py --enlarge VALUE input.bmp output.bmp
    python myWonderfulImProcApp.py --min WINDOW_SIZE input.bmp output.bmp
    python myWonderfulImProcApp.py --max WINDOW_SIZE input.bmp output.bmp
    python myWonderfulImProcApp.py --adaptive Smax input.bmp output.bmp
    
Commands:
    --brightness VALUE
        Modify brightness by adding VALUE to each pixel channel.
        Example: --brightness 20

    --contrast VALUE
        Modify contrast using a linear factor.
        1.0 = unchanged, 0.5 = lower contrast, 2.0 = higher contrast.

    --negative
        Invert each pixel channel: output = 255 - input.
        
    --hflip
        Flip the image horizontally (left to right).
        
    --vflip
        Flip the image vertically (top to bottom).
        
    --dflip
        Flip the image diagonally (transpose - swaps width and height).
        
    --shrink VALUE
        Shrink the image by an integer factor (e.g., 2 halves the dimensions).
        
    --enlarge VALUE
        Enlarge the image by an integer factor (e.g., 2 doubles the dimensions).

    --min WINDOW_SIZE
        Apply a minimum filter with a square window of size WINDOW_SIZE (odd integer >= 3).

    --max WINDOW_SIZE
        Apply a maximum filter with a square window of size WINDOW_SIZE (odd integer >= 3).

    --adaptive SMAX
        Apply an adaptive median filter with a maximum window size of Smax (odd integer >= 3).

    --help
        Display this help message.
""")

###########################
# HERE THE MAIN PART STARTS
###########################

def main():

    # check whether any command-line arguments were provided
    if len(sys.argv) == 1:
        print("No command line parameters given.")
        print("Use --help for available commands.")
        return

    # display the help message if requested
    if sys.argv[1] == "--help":
        printHelp()
        return

    # read the selected operation from the command line
    command = sys.argv[1]

    # brightness and contrast require an additional parameter
    if command in ("--brightness", "--contrast", "--shrink", "--enlarge", "--min", "--max", "--adaptive"):

        # check that the correct number of arguments was provided
        if len(sys.argv) != 5:
            print("Usage: command VALUE input.bmp output.bmp")
            return

        # store the operation parameter and file names
        param = sys.argv[2]
        input_file = sys.argv[3]
        output_file = sys.argv[4]

    # the negative & hflip operation does not require an additional parameter
    elif command in ("--negative", "--hflip", "--vflip", "--dflip"):
        if len(sys.argv) != 4:
            print(f"Usage: {command} input.bmp output.bmp")
            return

        # no additional parameter is needed for the negative operation
        param = None
        input_file = sys.argv[2]
        output_file = sys.argv[3]

    # handle commands that are not supported
    else:
        print("Unknown command:", command)
        print("Use --help for available commands.")
        return

    try:
        # open the input BMP image
        with Image.open(input_file) as image:

            # keep grayscale images in grayscale mode
            if image.mode == "L":
                mode = "L"
            else:
                # use RGB mode for color images
                mode = "RGB"

            # convert the image to the selected mode
            image = image.convert(mode)

            # store the image dimensions
            width, height = image.size

            # extract all pixels into a list
            pixels = list(image.getdata())

        # apply the selected image processing operation
        if command == "--brightness":
            pixels = doBrightness(pixels, param)

        elif command == "--contrast":
            pixels = doContrast(pixels, param)

        elif command == "--negative":
            pixels = doNegative(pixels)

        elif command == "--hflip":
            # hflip requires width and height to know where rows end
            pixels = doHflip(pixels, width, height)

        elif command == "--vflip":
            # vflip requires width and height to calculate row positions
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

        # create a new image with the original dimensions and mode
        result = Image.new(mode, (width, height))

        # insert the processed pixels into the new image
        result.putdata(pixels)

        # save the result in BMP format
        result.save(output_file, format="BMP")

        # confirm that processing was successful
        print("Processing completed successfully.")
        print("Output saved to:", output_file)

    # handle file errors and invalid numerical parameters
    except (OSError, ValueError) as error:
        print("Error:", error)


# run main() only when this file is executed directly
if __name__ == "__main__":
    main()
