API Documentation for descutils.lua

descutils.lua is a library for creating and managing graphical buttons in the ComputerCraft/Tweaked environment. The library provides a simple API for creating interactive user interface elements.
--------------------------------------------
Core Functions:

descutils.createButton(x, y, width, height)

Creates a new button and returns the button object.

Parameters:
    x, y - coordinates of the top-left corner of the button
    width, height - dimensions of the button

Returns: button object

Example:
lua:{
	local button = descutils.createButton(2, 3, 10, 3)
}
--------------------------------------------
Button Object Methods:
button:setColor(newColor)

Sets the background color of the button.

Parameters:
    newColor - color (number or color table from CC)

Returns: the button object itself (for method chaining)
--------------------------------------------
button:setTextColor(newColor)

Sets the text color of the button.

Parameters:
    newColor - color (number or color table from CC)

Returns: the button object itself
--------------------------------------------
button:setLabel(alignment, text)

Sets the button text and its alignment.

Parameters:
    alignment - alignment string (format: "VH", where V - vertical, H - horizontal)
    text - button text

Alignment formats:
    Vertical: "U" (top), "C" (center), "D" (bottom)
    Horizontal: "L" (left), "C" (center), "R" (right)
    Examples: "UL", "CC", "DR"

Returns: the button object itself
--------------------------------------------
button:setName(newName)

Sets a unique name for the button for identification.

Parameters:
    newName - string name of the button

Returns: the button object itself
--------------------------------------------
button:setVisible(isVisible)

Shows or hides the button.

Parameters:
    isVisible - boolean visibility value

Returns: the button object itself
--------------------------------------------
button:setEnabled(isEnabled)

Enables or disables the button.

Parameters:
    isEnabled - boolean activation value

Returns: the button object itself
--------------------------------------------
button:draw()

Renders the button on the screen.
--------------------------------------------
button:contains(clickX, clickY)

Checks if a point is inside the button.

Parameters:
    clickX, clickY - coordinates of the point

Returns: true if the point is inside the button, otherwise false
--------------------------------------------
Library Global Functions:

descutils.isClicked(clickX, clickY)

Checks for clicks on any of the created buttons.

Parameters:
    clickX, clickY - click coordinates

Returns:
    name - name of the clicked button (or nil)
    true/false - whether any button was clicked
--------------------------------------------
descutils.getButton(name)

Returns a button by name.

Parameters:
    name - button name

Returns: button object or nil
--------------------------------------------
descutils.removeButton(name)

Removes a button by name.

Parameters:
    name - name of the button to remove
--------------------------------------------
descutils.drawAll()

Renders all created buttons.
--------------------------------------------
descutils.clearAll()

Removes all buttons.
--------------------------------------------
descutils.getButtonCount()

Returns the number of created buttons.

Returns: number of buttons

Usage Example
lua:{

local descutils = require("descutils")

-- Create a button
	local myButton = descutils.createButton(5, 5, 15, 3)
		:setColor(colors.blue)
		:setTextColor(colors.white)
		:setLabel("CC", "Click me!")
		:setName("my_button")
		:setEnabled(true)

	-- Render all buttons
	descutils.drawAll()

	-- Handle clicks
	local event, button, x, y = os.pullEvent("mouse_click")
	local buttonName, clicked = descutils.isClicked(x, y)

	if clicked then
		print("Clicked button: " .. buttonName)
	end
}
Notes:
    Buttons automatically trim long text (adds "...")
    Disabled buttons are displayed in gray color
    All button methods support method chaining
    Coordinates and dimensions use the ComputerCraft system (1-based indexing)

(The code may contain unknown errors, please let me know if you find any)