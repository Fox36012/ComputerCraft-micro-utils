

-- brgb_viewer.lua
local colorConstants = {
    colors.white, colors.orange, colors.magenta, colors.lightBlue,
    colors.yellow, colors.lime, colors.pink, colors.gray,
    colors.lightGray, colors.cyan, colors.purple, colors.blue,
    colors.brown, colors.green, colors.red, colors.black
}

local function loadBRGB(filename)
    local file = fs.open(filename, "rb")
    if not file then
        return nil
    end
    
    -- Проверяем сигнатуру
    local signature = file.read(4)
    if signature ~= "BRGB" then
        file.close()
        return nil
    end
    
    -- Читаем размеры
    local width = string.byte(file.read(1)) * 256 + string.byte(file.read(1))
    local height = string.byte(file.read(1)) * 256 + string.byte(file.read(1))
    
    local pixelData = {}
    for y = 1, height do
        pixelData[y] = {}
        for x = 1, width do
            pixelData[y][x] = string.byte(file.read(1))
        end
    end
    
    file.close()
    return pixelData, width, height
end

local function displayBRGB(filename)
	term.setGraphicsMode(1)
	term.clear()
    local pixelData, width, height = loadBRGB(filename)
    if not pixelData then
        error("Cannot load BRGB file: " .. filename)
    end
    
    for y = 1, height do
        for x = 1, width do
            local colorIndex = pixelData[y][x]
            local colorValue = colorConstants[colorIndex + 1] -- +1 т.к. индексы в Lua с 1
            term.setPixel(x, y, colorValue)
        end
    end
    
    if os.pullEvent("key") then
       os.pullEvent("key") 
        
        
    end
    
    term.setGraphicsMode(0)
    return true
end

-- Основная программа
local args = {...}

if #args == 0 then
    print("Usage: brgb_viewer <path_to_brgb_file>")
    print("Example: brgb_viewer image.brgb")
    return
end

local filename = args[1]

-- Проверяем существование файла
if not fs.exists(filename) then
    print("File not found: " .. filename)
    return
end

-- Проверяем расширение файла
if not filename:match("%.brgb$") then
    print("Warning: File extension is not .brgb")
end

-- Запускаем отображение
local success, err = pcall(function()
    displayBRGB(filename)
end)

if not success then
    print("Error: " .. err)
end
