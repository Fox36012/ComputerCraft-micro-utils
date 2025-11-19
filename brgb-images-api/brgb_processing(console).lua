-- Палитра цветов ComputerCraft в HEX для квантования
local palette = {
    {0xF0, 0xF0, 0xF0},{0xF2, 0xB2, 0x33},{0xE5, 0x7F, 0xD8},{0x99, 0xB2, 0xF2},
    {0xDE, 0xDE, 0x6C},{0x7F, 0xCC, 0x19},{0xF2, 0xB2, 0xCC},{0x4C, 0x4C, 0x4C},
    {0x99, 0x99, 0x99},{0x4C, 0x99, 0xB2},{0xB2, 0x66, 0xE5},{0x33, 0x66, 0xCC},
    {0x7F, 0x66, 0x4C},{0x57, 0xA6, 0x4E},{0xCC, 0x4C, 0x4C},{0x11, 0x11, 0x11}
}

-- Таблица для преобразования индексов в константы colors.*
local colorConstants = {
    colors.white, colors.orange, colors.magenta, colors.lightBlue,
    colors.yellow, colors.lime, colors.pink, colors.gray,
    colors.lightGray, colors.cyan, colors.purple, colors.blue,
    colors.brown, colors.green, colors.red, colors.black
}
-- Функция для вычисления расстояния между цветами
local function colorDistance(r1, g1, b1, r2, g2, b2)
    return math.sqrt((r1 - r2)^2 + (g1 - g2)^2 + (b1 - b2)^2)
end

-- Функция квантования - нахождение ближайшего цвета в палитре
local function quantizeColor(r, g, b)
    local bestIndex = 1
    local bestDistance = colorDistance(r, g, b, palette[1][1], palette[1][2], palette[1][3])
    
    for i = 2, #palette do
        local dist = colorDistance(r, g, b, palette[i][1], palette[i][2], palette[i][3])
        if dist < bestDistance then
            bestDistance = dist
            bestIndex = i
        end
    end
    
    return bestIndex - 1 -- возвращаем индекс от 0 до 15
end

-- Функция дизеринга по Флойду-Стейнбергу
local function floydSteinbergDither(bmpData, width, height)
    local result = {}
    
    -- Создаем копию данных для обработки
    for y = 1, height do
        result[y] = {}
        for x = 1, width do
            result[y][x] = {bmpData[y][x][1], bmpData[y][x][2], bmpData[y][x][3]}
        end
    end
    
    -- Применяем дизеринг
    for y = 1, height do
        for x = 1, width do
            local oldR, oldG, oldB = result[y][x][1], result[y][x][2], result[y][x][3]
            
            -- Находим ближайший цвет
            local newColorIndex = quantizeColor(oldR, oldG, oldB)
            local newR, newG, newB = palette[newColorIndex + 1][1], palette[newColorIndex + 1][2], palette[newColorIndex + 1][3]
            
            -- Записываем результат (только индекс цвета)
            result[y][x] = newColorIndex
            
            -- Вычисляем ошибку
            local errR = oldR - newR
            local errG = oldG - newG
            local errB = oldB - newB
            
            -- Распространяем ошибку на соседние пиксели
            if x < width then
                -- Пиксель справа
                if type(result[y][x+1]) == "table" then
                    local rightR, rightG, rightB = result[y][x+1][1], result[y][x+1][2], result[y][x+1][3]
                    result[y][x+1] = {
                        math.max(0, math.min(255, rightR + errR * 7/16)),
                        math.max(0, math.min(255, rightG + errG * 7/16)),
                        math.max(0, math.min(255, rightB + errB * 7/16))
                    }
                end
            end
            
            if y < height then
                if x > 1 then
                    -- Пиксель слева снизу
                    if type(result[y+1][x-1]) == "table" then
                        local leftDownR, leftDownG, leftDownB = result[y+1][x-1][1], result[y+1][x-1][2], result[y+1][x-1][3]
                        result[y+1][x-1] = {
                            math.max(0, math.min(255, leftDownR + errR * 3/16)),
                            math.max(0, math.min(255, leftDownG + errG * 3/16)),
                            math.max(0, math.min(255, leftDownB + errB * 3/16))
                        }
                    end
                end
                
                -- Пиксель снизу
                if type(result[y+1][x]) == "table" then
                    local downR, downG, downB = result[y+1][x][1], result[y+1][x][2], result[y+1][x][3]
                    result[y+1][x] = {
                        math.max(0, math.min(255, downR + errR * 5/16)),
                        math.max(0, math.min(255, downG + errG * 5/16)),
                        math.max(0, math.min(255, downB + errB * 5/16))
                    }
                end
                
                if x < width then
                    -- Пиксель справа снизу
                    if type(result[y+1][x+1]) == "table" then
                        local rightDownR, rightDownG, rightDownB = result[y+1][x+1][1], result[y+1][x+1][2], result[y+1][x+1][3]
                        result[y+1][x+1] = {
                            math.max(0, math.min(255, rightDownR + errR * 1/16)),
                            math.max(0, math.min(255, rightDownG + errG * 1/16)),
                            math.max(0, math.min(255, rightDownB + errB * 1/16))
                        }
                    end
                end
            end
        end
    end
    
    return result
end

-- Функция для чтения BMP файла
local function readBMP(filename)
    local file = fs.open(filename, "rb")
    if not file then
        error("Cannot open file: " .. filename)
    end
    
    -- Читаем заголовок
    local signature = file.read(2)
    if signature ~= "BM" then
        file.close()
        error("Not a BMP file")
    end
    
    -- Пропускаем до информации о размере (смещение 18 от начала файла)
    file.seek("set", 18)
    
    -- Читаем ширину и высоту как 4-байтные little-endian числа
    local widthBytes = {string.byte(file.read(1)), string.byte(file.read(1)), string.byte(file.read(1)), string.byte(file.read(1))}
    local heightBytes = {string.byte(file.read(1)), string.byte(file.read(1)), string.byte(file.read(1)), string.byte(file.read(1))}
    
    local width = widthBytes[1] + widthBytes[2] * 256 + widthBytes[3] * 65536 + widthBytes[4] * 16777216
    local height = heightBytes[1] + heightBytes[2] * 256 + heightBytes[3] * 65536 + heightBytes[4] * 16777216
    
    -- Пропускаем до начала пиксельных данных (смещение 54 от начала для 24-bit BMP)
    file.seek("set", 54)
    
    local bmpData = {}
    local rowSize = math.ceil((width * 3) / 4) * 4  -- Выравнивание строк до кратного 4 байтам
    local padding = rowSize - width * 3
    
    -- Читаем пиксельные данные (BMP хранится снизу вверх)
    for y = height, 1, -1 do
        bmpData[y] = {}
        for x = 1, width do
            local b = string.byte(file.read(1))
            local g = string.byte(file.read(1))
            local r = string.byte(file.read(1))
            bmpData[y][x] = {r, g, b}
        end
        -- Пропускаем padding байты в конце строки
        if padding > 0 then
            file.seek("cur", padding)
        end
    end
    
    file.close()
    return bmpData, width, height
end

-- Функция для сохранения в формат .brgb
local function saveBRGB(filename, pixelData, width, height)
    local file = fs.open(filename, "wb")
    
    -- Заголовок: сигнатура + размеры
    file.write("BRGB")
    file.write(string.char(math.floor(width / 256), width % 256))
    file.write(string.char(math.floor(height / 256), height % 256))
    
    -- Данные пикселей (только индексы цветов 0-15)
    for y = 1, height do
        for x = 1, width do
            file.write(string.char(pixelData[y][x]))
        end
    end
    
    file.close()
end

-- Основная функция обработки
local function processBMP(inputFile, outputFile, useDithering)
    print("Reading BMP file: " .. inputFile)
    local bmpData, width, height = readBMP(inputFile)
    
    print("Image size: " .. width .. "x" .. height)
    print("Processing image...")
    
    local processedData = {}
    
    if useDithering then
        print("Using Floyd-Steinberg dithering")
        processedData = floydSteinbergDither(bmpData, width, height)
    else
        print("Using simple color quantization")
        for y = 1, height do
            processedData[y] = {}
            for x = 1, width do
                local r, g, b = bmpData[y][x][1], bmpData[y][x][2], bmpData[y][x][3]
                processedData[y][x] = quantizeColor(r, g, b)
            end
        end
    end
    
    print("Saving BRGB file: " .. outputFile)
    saveBRGB(outputFile, processedData, width, height)
    print("Done! BRGB file saved successfully")
    
    return width, height
end

-- Функция для отображения справки
local function showHelp()
    print("BRGB Image Processor for ComputerCraft")
    print("Usage: brgb_process <bmp_file> <brgb_file> <useDithering>")
    print("")
    print("Arguments:")
    print("  bmp_file      - Path to input BMP file")
    print("  brgb_file     - Path for output BRGB file")
    print("  useDithering  - 'true' for dithering, 'false' for simple quantization")
    print("")
    print("Examples:")
    print("  brgb_process image.bmp image.brgb true")
    print("  brgb_process photo.bmp result.brgb false")
end

-- Основная функция
local function main(args)
    if #args < 3 then
        showHelp()
        return
    end
    
    local inputFile = args[1]
    local outputFile = args[2]
    local useDithering = args[3]
    
    -- Проверяем существование входного файла
    if not fs.exists(inputFile) then
        print("Error: Input file '" .. inputFile .. "' not found")
        return
    end
    
    -- Преобразуем useDithering в boolean
    if useDithering == "true" then
        useDithering = true
    elseif useDithering == "false" then
        useDithering = false
    else
        print("Error: useDithering must be 'true' or 'false'")
        showHelp()
        return
    end
    local success, width, height = pcall(processBMP, inputFile, outputFile, useDithering)
    if success then
        print("Successfully converted " .. width .. "x" .. height .. " image")
    else
        print("Error during processing: " .. tostring(width)) -- width содержит сообщение об ошибке в этом случае
    end
end

-- Запускаем программу если файл выполняется напрямую
if not shell then
    print("This program must be run from ComputerCraft shell")
else
    main({...})
end