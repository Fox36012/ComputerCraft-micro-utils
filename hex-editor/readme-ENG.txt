Hexadecimal editor for viewing and editing binary files in ComputerCraft/Tweaked.

works only with existing files (This will be corrected in the future)

Main Features:
    File viewing - display in hex and ASCII format
    Editing - step-by-step byte modification via hex input
    Navigation - arrow key movement, scrolling for large files
    Saving - automatic save changes (Tab)

Interface:
    Left panel - offset (file position)
    Center panel - hex byte representation (16 columns)
    Right panel - ASCII character representation
    Cursor - highlight for current editable cell

Controls:
    Arrow keys - cursor movement
    0-9, A-F - hex value input
    Tab - save file
    Escape - exit editor

Features:
    Automatic terminal size detection
    Support for files of any size with virtual scrolling
    Protection against file boundary overflows
    Input hex value validation
	
(The code may contain unknown errors, please let me know if you find any)