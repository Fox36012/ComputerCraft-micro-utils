local term_sizeX,term_sizeY = term.getSize()
local stack_pointer={1,1}
local pointer={11,2}
local table_offset = 0
local running = true
local edit_filepath = ""

local data = {}
local data_size = 0

function load_file(filepath)
    local file = fs.open(filepath, "rb")
    if not file then
        error("Cannot open file: " .. filepath)
    end
    
    local filedata = {}
    local index = 1
    while true do
        local byte = file.read()
        if byte == nil then break end
        filedata[index] = byte
        index = index + 1
    end
    file.close()
    
    data_size = index - 1
    
    -- Устанавливаем метатаблицу после загрузки данных
    setmetatable(filedata, {__index = function() return 0 end})
    
    return filedata
end

function save_file(filepath, data_table)
    local file = fs.open(filepath, "wb")
    if not file then
        error("Cannot open file for writing: " .. filepath)
    end
    
    -- Сохраняем данные, используя data_size для определения размера
    for i = 1, data_size do
        file.write(data_table[i])
    end
    file.close()
end

local hex_keys = {}
local function addKey(key, value)
    if key ~= nil then
        hex_keys[key] = value
    end
end

addKey(keys.zero, 0)
addKey(keys.one, 1)
addKey(keys.two, 2)
addKey(keys.three, 3)
addKey(keys.four, 4)
addKey(keys.five, 5)
addKey(keys.six, 6)
addKey(keys.seven, 7)
addKey(keys.eight, 8)
addKey(keys.nine, 9)
addKey(keys.a, 0xA)
addKey(keys.b, 0xB)
addKey(keys.c, 0xC)
addKey(keys.d, 0xD)
addKey(keys.e, 0xE)
addKey(keys.f, 0xF)

local input_nibble = nil

local function draw()
    term.setBackgroundColor(colors.black)
    term.setTextColor(colors.white)
    term.clear()
    term.setCursorPos(1,1)
    term.blit("| Offset  |00|01|02|03|04|05|06|07|08|09|0A|0B|0C|0D|0E|0F|   decoded text  |",
              "11111111111111111111111111111111111111111111111111111111111111111111111111111",
              "77777777777777777777777777777777777777777777777777777777777777777777777777777")
    for i=1, term_sizeY do
        local row_offset = (i-1) + table_offset
        local offset = string.format("%07x", row_offset)
        term.setCursorPos(1,i+1)
        -- Формируем hex строку и декодированный текст для текущей строки
        local hex_parts = {}
        local decoded_chars = {}
        for col=1, 16 do
            local data_index = col + 16 * row_offset
            local byte_value = data[data_index] -- Используем прямое обращение к data
            -- Hex представление
            hex_parts[col] = string.format("%02x", byte_value)
            -- Декодированный текст (заменяем непечатаемые символы на точку)
            if byte_value >= 32 and byte_value <= 126 then
                decoded_chars[col] = string.char(byte_value)
            else
                decoded_chars[col] = "."
            end
        end
        local hex_line = table.concat(hex_parts, "|")
        local decoded_text = table.concat(decoded_chars)
        term.blit("|"..offset.."0|"..hex_line.."| "..decoded_text.." |",
        "f11111111f00f00f00f00f00f00f00f00f00f00f00f00f00f00f00f00f000000000000000000f",
        "97777777799999999999999999999999999999999999999999999999997777777777777777779")
    end
    -- Отображение курсора
    term.setCursorPos(pointer[1],pointer[2])
    local current_address = stack_pointer[1] + 16 * (stack_pointer[2]+table_offset-1)
    term.blit(string.format("%02x", data[current_address]),"ee","77") -- Прямое обращение к data
end

local function control()
    local _,key = os.pullEvent("key")
    if key==keys.up then
        input_nibble = nil
        if pointer[2]~=2 then
            pointer[2] = pointer[2] - 1
            stack_pointer[2] = stack_pointer[2] - 1
        elseif table_offset > 0 then
            table_offset = table_offset - 1
        end
    elseif key==keys.down then
        input_nibble = nil
        if pointer[2]~= term_sizeY then
            pointer[2] = pointer[2] + 1
            stack_pointer[2] = stack_pointer[2] + 1
        else
            table_offset = table_offset + 1
        end
    elseif key==keys.left then
        input_nibble = nil
        if pointer[1]~= 11 then
            pointer[1] = pointer[1] - 3
            stack_pointer[1] = stack_pointer[1] - 1
        else
            pointer[1] = 56
            stack_pointer[1] = 16
            if pointer[2]~= 2 then
                pointer[2] = pointer[2] - 1
                stack_pointer[2] = stack_pointer[2] - 1
            elseif pointer[2] == term_sizeY then
                table_offset = table_offset - 1
            end    
        end
    elseif key==keys.right then
        input_nibble = nil
        if pointer[1]<= 55 then
            pointer[1] = pointer[1] + 3
            stack_pointer[1] = stack_pointer[1] + 1
        else
            pointer[1] = 11
            stack_pointer[1] = 1
            if pointer[2]~= term_sizeY then
                pointer[2] = pointer[2] + 1
                stack_pointer[2] = stack_pointer[2] + 1
            elseif pointer[2] == term_sizeY then
                table_offset = table_offset + 1
            end    
        end
    elseif key==keys.escape then
        running = false
    elseif key==keys.tab then
        save_file(edit_filepath, data)
    else
        local hex_value = hex_keys[key]
        if hex_value ~= nil then
            local current_address = stack_pointer[1] + 16 * (stack_pointer[2]+table_offset - 1)
            
            -- Обновляем data_size если редактируем за пределами текущего размера
            if current_address > data_size then
                data_size = current_address
            end
            
            if input_nibble == nil then
                input_nibble = hex_value
                data[current_address] = hex_value * 16 -- Прямое обращение к data
            else
                data[current_address] = input_nibble * 16 + hex_value -- Прямое обращение к data
                input_nibble = nil
                
                -- Автоперемещение после ввода
                if pointer[1] <= 55 then
                    pointer[1] = pointer[1] + 3
                    stack_pointer[1] = stack_pointer[1] + 1
                else
                    pointer[1] = 11
                    stack_pointer[1] = 1
                    if pointer[2]~= term_sizeY then
                        pointer[2] = pointer[2] + 1
                        stack_pointer[2] = stack_pointer[2] + 1
                    elseif pointer[2] == term_sizeY then
                        table_offset = table_offset + 1
                    end    
                end
            end
        else
            input_nibble = nil
        end
    end
end

function main(filepath)
    data = load_file(filepath)
    while running do
        draw()
        control()
    end
end

local args = {...}

if #args == 0 then
    print("Usage: hex_editor <path_to_file>")
    return
end

local filename = args[1]

-- Проверяем существование файла
if not fs.exists(filename) then
    print("File not found: " .. filename)
    return
end

-- Запускаем отображение
local success, err = pcall(function()
    edit_filepath = filename
    main(filename)
end)

if not success then
    print("Error: " .. err)
end