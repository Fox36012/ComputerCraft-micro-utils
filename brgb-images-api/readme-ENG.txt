Image processing library for BMP format and display in ComputerCraft/Tweaked.

ATTENTION: WORKS ONLY IN THE CraftOS-pc ENVIRONMENT!!!

files:
	brgb_processing_api - original code
	brgb_processing(console) - console version (Usage: brgb_process <bmp_file> <brgb_file> <useDithering>)
	brgb_processing_api(optim) - optimized version
	brgb_viewer - can only show the image (Usage: brgb_viewer <path_to_brgb_file>)

Main Features:
    BMP file reading - loading 24-bit BMP images
    Color conversion - converting RGB to ComputerCraft palette (16 colors)
    Floyd-Steinberg dithering - improved color conversion quality
    Custom LCBI format - compact image storage
    Image display - output to screen via graphics mode

Key Functions:
    processBMP() - converts BMP to LCBI with dithering
    displayLCBI() - displays LCBI file on screen
    previewImage() - image preview in graphics mode
    loadLCBI()/saveLCBI() - work with custom format

Features:
    Dithering algorithm support for smooth color transitions
    Automatic nearest color matching from CC palette
    Efficient data storage (1 byte per pixel)
    File reading error handling

(The code may contain unknown errors, please let me know if you find any)