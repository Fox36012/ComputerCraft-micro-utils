local fm = {}
fm.state = {
	dir           = ""    	,
	fullPath      = ""    	,
	list_cursor   = 1     	,
	list_height   = 0		,
	term_x        = 40    	,
	term_y        = 15   	,
	scroll_offset = 0     	,
	dir_list      = {}    	,
	show_help     = false	,
	running       = true   ,
	show_action_menu = false,
	action_menu_cursor = 1,
	show_delete_confirm = false
}

fm.state.list_height = fm.state.term_y-2

function fm.split(symb, sep)
  local result = {}
  local pattern = string.format("([^%s]+)", sep)
  for match in symb:gmatch(pattern) do
    table.insert(result, match)
  end
  return result
end

function fm.getDisplayList()
    local display_list = {}
    if fm.state.dir ~= "" then
        table.insert(display_list, "..")
    end
    for _, item in ipairs(fm.state.dir_list) do
        table.insert(display_list, item)
    end
    return display_list
end

function fm.formatSize(size)
    if size < 1024 then
        return string.format("%d B", size)
    elseif size < 1024 * 1024 then
        return string.format("%.1f KB", size / 1024)
    elseif size < 1024 * 1024 * 1024 then
        return string.format("%.1f MB", size / (1024 * 1024))
    else
        return string.format("%.1f GB", size / (1024 * 1024 * 1024))
    end
end

function fm.drawFileList()
    local display_list = fm.getDisplayList()
	local visible_items = math.min(#display_list - fm.state.scroll_offset, fm.state.list_height)
	
	for i=1,visible_items do
		local file_index=i+fm.state.scroll_offset
		local selected=display_list[file_index]
		
		if selected == ".." then
			term.setBackgroundColor(colors.blue)
			term.setTextColor(colors.white)
			term.setCursorPos(1,i+1)
			term.write(string.char(0x7F).." ..")
			
			term.setCursorPos(15, i+1)
			term.setBackgroundColor(colors.gray)
			term.setTextColor(colors.lightGray)
			term.write('|')
			
			term.setCursorPos(23, i+1)
			term.write('|')
		else
			fm.state.fullPath=fm.state.dir..selected
			term.setBackgroundColor(colors.cyan)
			term.setTextColor(colors.white)
			term.setCursorPos(1,i+1)
			
			if string.len(selected)>12 then
				term.write(string.char(0x7F).." "..string.sub(selected, 1, 11)..".")
			else
				term.write(string.char(0x7F).." "..selected)
			end
			
			term.setCursorPos(15, i+1)
			term.setBackgroundColor(colors.gray)
			term.setTextColor(colors.lightGray)
			
			if not fs.isDir(fm.state.fullPath) then
				local size = fs.getSize(fm.state.fullPath)
				local size_text = fm.formatSize(size)
				term.write('|'..size_text)
			else
				term.write('|')
			end
			
			term.setCursorPos(23, i+1)
			
			if fs.isReadOnly(fm.state.fullPath)then
				term.write('|RO')
			else
				term.write('|')
			end
		end
	end
	
	term.setTextColor(colors.white)
	
	if fm.state.list_cursor>=fm.state.scroll_offset+1 and 
		fm.state.list_cursor<=fm.state.scroll_offset+fm.state.list_height then
		local cursor_pos = fm.state.list_cursor-fm.state.scroll_offset+1
		paintutils.drawPixel(1, cursor_pos, colors.green)
	end
	
	if #display_list > fm.state.list_height then
		local scroll_pos=math.floor((fm.state.scroll_offset/(#display_list-fm.state.list_height))*(fm.state.list_height-1)+2)
		term.setCursorPos(fm.state.term_x, scroll_pos)
		term.write("#")
	end
end

function fm.drawActionMenu()
	local menu_width = 20
	local menu_height = 6
	local x = math.floor((fm.state.term_x - menu_width) / 2)
	local y = math.floor((fm.state.term_y - menu_height) / 2)
	
	paintutils.drawFilledBox(x, y, x + menu_width, y + menu_height, colors.white)
	paintutils.drawBox(x, y, x + menu_width, y + menu_height, colors.black)
	
	term.setBackgroundColor(colors.white)
	term.setTextColor(colors.black)
	term.setCursorPos(x + 2, y + 1)
	
	local display_list = fm.getDisplayList()
	local filename = display_list[fm.state.list_cursor]
	if string.len(filename) > 15 then
		filename = string.sub(filename, 1, 12) .. "..."
	end
	term.write("File: " .. filename)
	
	local options = {"Execute", "Edit", "Delete"}
	for i, option in ipairs(options) do
		term.setCursorPos(x + 2, y + 2 + i)
		if i == fm.state.action_menu_cursor then
			term.setBackgroundColor(colors.green)
			term.setTextColor(colors.white)
			term.write(option)
			term.setBackgroundColor(colors.white)
			term.setTextColor(colors.black)
		else
			term.setBackgroundColor(colors.white)
			term.setTextColor(colors.black)
			term.write(option)
		end
	end
end

function fm.drawDeleteConfirm()
	local menu_width = 30
	local menu_height = 5
	local x = math.floor((fm.state.term_x - menu_width) / 2)
	local y = math.floor((fm.state.term_y - menu_height) / 2)
	
	paintutils.drawFilledBox(x, y, x + menu_width, y + menu_height, colors.white)
	paintutils.drawBox(x, y, x + menu_width, y + menu_height, colors.black)
	
	term.setBackgroundColor(colors.white)
	term.setTextColor(colors.black)
	term.setCursorPos(x + 2, y + 1)
	term.write("Confirm deletion")
	
	local display_list = fm.getDisplayList()
	local filename = display_list[fm.state.list_cursor]
	if string.len(filename) > 25 then
		filename = string.sub(filename, 1, 22) .. "..."
	end
	term.setCursorPos(x + 2, y + 2)
	term.write(filename)
	
	term.setCursorPos(x + 2, y + 3)
	term.write("Are you sure?")
	
	term.setCursorPos(x + 2, y + 4)
	term.setBackgroundColor(colors.red)
	term.setTextColor(colors.white)
	term.write("[ENTER] Delete")
	
	term.setCursorPos(x + 18, y + 4)
	term.setBackgroundColor(colors.gray)
	term.setTextColor(colors.white)
	term.write("[ESC] Cancel")
end

function fm.ui()
	term.clear()
	
	paintutils.drawFilledBox(1, 1, fm.state.term_x, fm.state.term_y, colors.gray)
	paintutils.drawLine(1, 1, fm.state.term_x, 1, colors.cyan)
	term.setCursorPos(1, 1)
	term.write("File Man 2| [F1]")
	
	if fm.state.show_help then
		fm.drawHelp()
	end
	
	term.setCursorPos(1, fm.state.term_y)
	term.write("path:")
	term.write(fm.state.dir)
end

function fm.control(key)
	key = key or ""
	fm.state.dir_list = fs.list(fm.state.dir) or {}
	local display_list = fm.getDisplayList()
	
	if fm.state.show_delete_confirm then
		if key == keys.enter then
			local selected = display_list[fm.state.list_cursor]
			if selected ~= ".." then
				fm.state.fullPath = fm.state.dir..selected
				if not fs.isReadOnly(fm.state.fullPath) then
					fs.delete(fm.state.fullPath)
				end
			end
			fm.state.show_delete_confirm = false
		elseif key == keys.escape then
			fm.state.show_delete_confirm = false
		end
		return
	end
	
	if fm.state.show_action_menu then
		if key == keys.up and fm.state.action_menu_cursor > 1 then
			fm.state.action_menu_cursor = fm.state.action_menu_cursor - 1
		elseif key == keys.down and fm.state.action_menu_cursor < 3 then
			fm.state.action_menu_cursor = fm.state.action_menu_cursor + 1
		elseif key == keys.enter then
			local selected = display_list[fm.state.list_cursor]
			fm.state.fullPath = fm.state.dir..selected
			
			if fm.state.action_menu_cursor == 1 then
				local ext = string.match(fm.state.fullPath, "%.([^%.]+)$")
				if ext == "lua" then
					multishell.launch({}, fm.state.fullPath)
				else
					shell.run(fm.state.fullPath)
				end
			elseif fm.state.action_menu_cursor == 2 then
				shell.run("edit", fm.state.fullPath)
			elseif fm.state.action_menu_cursor == 3 then
				if selected ~= ".." then
					fm.state.show_action_menu = false
					fm.state.show_delete_confirm = true
					return
				end
			end
			fm.state.show_action_menu = false
		elseif key == keys.escape then
			fm.state.show_action_menu = false
		elseif key == keys.one then
			local selected = display_list[fm.state.list_cursor]
			fm.state.fullPath = fm.state.dir..selected
			local ext = string.match(fm.state.fullPath, "%.([^%.]+)$")
			if ext == "lua" then
				multishell.launch({}, fm.state.fullPath)
			else
				shell.run(fm.state.fullPath)
			end
			fm.state.show_action_menu = false
		elseif key == keys.two then
			local selected = display_list[fm.state.list_cursor]
			fm.state.fullPath = fm.state.dir..selected
			shell.run("edit", fm.state.fullPath)
			fm.state.show_action_menu = false
		elseif key == keys.three then
			local selected = display_list[fm.state.list_cursor]
			if selected ~= ".." then
				fm.state.show_action_menu = false
				fm.state.show_delete_confirm = true
			end
		end
		return
	end
  
	if key == keys.up and fm.state.list_cursor > 1 then
		fm.state.list_cursor = fm.state.list_cursor - 1
		if fm.state.list_cursor <= fm.state.scroll_offset then
			fm.state.scroll_offset = math.max(0, fm.state.scroll_offset - 1)
		end
  
	elseif key == keys.down and fm.state.list_cursor < #display_list then
		fm.state.list_cursor = fm.state.list_cursor + 1
		if fm.state.list_cursor > fm.state.scroll_offset + fm.state.list_height then
			fm.state.scroll_offset = math.min(#display_list - fm.state.list_height, fm.state.scroll_offset + 1)
		end
  
	elseif key == keys.enter then
		if #display_list > 0 then
			local selected = display_list[fm.state.list_cursor]
			
			if selected == ".." then
				local path_parts = fm.split(fm.state.dir, "/")
				table.remove(path_parts, #path_parts)
				fm.state.dir = table.concat(path_parts, "/")
				if fm.state.dir ~= "" then
					fm.state.dir = fm.state.dir .. "/"
				end
				fm.state.list_cursor = 1
				fm.state.scroll_offset = 0
			else
				fm.state.fullPath = fm.state.dir..selected
				if fs.isDir(fm.state.fullPath) then
					fm.state.dir = fm.state.dir..selected.."/"
					fm.state.list_cursor = 1
					fm.state.scroll_offset = 0
				else
					fm.state.show_action_menu = true
					fm.state.action_menu_cursor = 1
				end
			end
		end
	
	elseif key == keys.delete then
		if #display_list > 0 then
			local selected = display_list[fm.state.list_cursor]
			if selected ~= ".." then
				fm.state.show_delete_confirm = true
			end
		end
    
	elseif key == keys.backspace then
		if fm.state.dir ~= "" then
			local path_parts = fm.split(fm.state.dir, "/")
			table.remove(path_parts, #path_parts)
			fm.state.dir = table.concat(path_parts, "/")
			if fm.state.dir ~= "" then
				fm.state.dir = fm.state.dir .. "/"
			end
			fm.state.list_cursor = 1
			fm.state.scroll_offset = 0
		end
	
	elseif key == keys.home then
		fm.state.dir = ""
		fm.state.list_cursor = 1
		fm.state.scroll_offset = 0
  
	elseif key == keys.f1 then
		fm.state.show_help = not fm.state.show_help
	
	elseif key == keys.tab then
		fm.state.running = false
	end
end

while fm.state.running do
	fm.state.dir_list = fs.list(fm.state.dir) or {}
	fm.ui()
	fm.drawFileList()
	
	if fm.state.show_action_menu then
		fm.drawActionMenu()
	elseif fm.state.show_delete_confirm then
		fm.drawDeleteConfirm()
	end
	
	event, key = os.pullEvent("key")
	fm.control(key)
end
