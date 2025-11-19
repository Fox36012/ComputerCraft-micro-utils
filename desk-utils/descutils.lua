-- descutils.lua
local descutils = {}
descutils.buttons = {}

-- Функция для преобразования цвета в число
local function resolveColor(color)
    if type(color) == "number" then
        return color
    elseif type(color) == "table" then
        -- Если это таблица цвета из CC, пытаемся получить числовое значение
        for name, value in pairs(colors) do
            if type(value) == "number" and color == colors[name] then
                return value
            end
        end
    end
    -- Fallback на белый цвет
    return colors.white
end

-- Функция для обрезки текста
local function trimText(text, width)
    local textLen = string.len(text)
    if textLen > width then
        return string.sub(text, 1, width - 1) .. "."
    end
    return text
end

-- Функция расчета позиции текста (исправленная)
local function calculateTextPosition(align, label, width, height)
    -- Преобразуем align в строку, если это таблица
    local alignStr = align
    if type(align) == "table" then
        alignStr = "CC" -- значение по умолчанию
    end
    
    local text = trimText(label, width)
    local textLen = string.len(text)
    local x, y = 1, 1
    
    -- Получаем первый и второй символы выравнивания
    local vertAlign = string.sub(alignStr, 1, 1)
    local horzAlign = string.sub(alignStr, 2, 2)
    
    -- Вертикальное выравнивание
    if vertAlign == "U" then 
        y = 1
    elseif vertAlign == "C" then 
        y = math.floor(height / 2)
    elseif vertAlign == "D" then 
        y = height
    else
        y = math.floor(height / 2) -- по умолчанию по центру
    end
    
    -- Горизонтальное выравнивание
    if horzAlign == "L" then 
        x = 1
    elseif horzAlign == "C" then 
        x = math.floor((width - textLen) / 2) + 1
    elseif horzAlign == "R" then 
        x = width - textLen + 1
    else
        x = math.floor((width - textLen) / 2) + 1 -- по умолчанию по центру
    end
    
    -- Ограничение координат
    if x < 1 then x = 1 end
    if x > width then x = width end
    if y < 1 then y = 1 end
    if y > height then y = height end
    
    return x, y, text
end

function descutils.createButton(x, y, width, height)
    local button = {
        x = x,
        y = y,
        w = width,
        h = height,
        color = colors.white,
        textColor = colors.black,
        label = "",
        align = "CC", -- строка по умолчанию
        name = "button_" .. tostring(math.random(1000, 9999)),
        visible = true,
        enabled = true
    }
    
    -- Метод для установки цвета фона
    function button:setColor(newColor)
        self.color = resolveColor(newColor)
        return self
    end

    -- Метод для установки цвета текста
    function button:setTextColor(newColor)
        self.textColor = resolveColor(newColor)
        return self
    end

    -- Метод для установки текста и выравнивания
    function button:setLabel(alignment, text)
        if alignment ~= nil then
            -- Преобразуем alignment в строку, если это таблица
            if type(alignment) == "table" then
                self.align = "CC"
            else
                self.align = tostring(alignment)
            end
        end
        if text ~= nil then
            self.label = tostring(text)
        end
        return self
    end
    
    -- Метод для установки имени кнопки
    function button:setName(newName)
        if descutils.buttons[self.name] then
            descutils.buttons[self.name] = nil
        end
        self.name = tostring(newName)
        descutils.buttons[self.name] = self
        return self
    end
    
    -- Метод для показа/скрытия кнопки
    function button:setVisible(isVisible)
        self.visible = isVisible
        return self
    end
    
    -- Метод для включения/выключения кнопки
    function button:setEnabled(isEnabled)
        self.enabled = isEnabled
        return self
    end

    -- Метод для отрисовки кнопки
    function button:draw()
        if not self.visible then
            return
        end
        
        local oldBg = term.getBackgroundColor()
        local oldText = term.getTextColor()
        
        -- Устанавливаем цвета
        local bgColor = self.color
        local txtColor = self.textColor
        
        -- Если кнопка отключена, делаем ее серой
        if not self.enabled then
            bgColor = colors.gray
            txtColor = colors.lightGray
        end
        
        term.setBackgroundColor(bgColor)
        term.setTextColor(txtColor)
        
        -- Рисуем область кнопки
        for dy = self.y, self.y + self.h - 1 do
            term.setCursorPos(self.x, dy)
            term.write(string.rep(" ", self.w))
        end
        
        -- Рисуем текст, если кнопка включена
        if self.enabled or not self.enabled then
            local tx, ty, text = calculateTextPosition(
                self.align, 
                self.label, 
                self.w, 
                self.h
            )
            
            term.setCursorPos(self.x + tx - 1, self.y + ty - 1)
            term.write(text)
        end
        
        -- Восстанавливаем цвета
        term.setBackgroundColor(oldBg)
        term.setTextColor(oldText)
    end
    
    -- Метод для проверки, находится ли точка внутри кнопки
    function button:contains(clickX, clickY)
        if not self.visible or not self.enabled then
            return false
        end
        
        return clickX >= self.x and 
               clickX < self.x + self.w and
               clickY >= self.y and 
               clickY < self.y + self.h
    end

    -- Добавляем кнопку в таблицу
    descutils.buttons[button.name] = button

    return button
end

-- Функция проверки клика по любой кнопке
function descutils.isClicked(clickX, clickY)
    for name, button in pairs(descutils.buttons) do
        if button:contains(clickX, clickY) then
            return name, true
        end
    end
    return nil, false
end

-- Функция для получения кнопки по имени
function descutils.getButton(name)
    return descutils.buttons[name]
end

-- Функция для удаления кнопки
function descutils.removeButton(name)
    descutils.buttons[name] = nil
end

-- Функция для отрисовки всех кнопок
function descutils.drawAll()
    for _, button in pairs(descutils.buttons) do
        button:draw()
    end
end

-- Функция для очистки всех кнопок
function descutils.clearAll()
    descutils.buttons = {}
end

-- Функция для получения количества кнопок
function descutils.getButtonCount()
    local count = 0
    for _ in pairs(descutils.buttons) do
        count = count + 1
    end
    return count
end

return descutils