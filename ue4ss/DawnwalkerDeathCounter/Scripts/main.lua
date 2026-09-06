local UEHelpers = require("UEHelpers")

local COUNTER_PATH = "Mods/DawnwalkerDeathCounter/counter.txt"
local POLL_MS = 250
local DEAD_THRESHOLD = 0.01

local count = 0
local wasAlive = false
local deathLatched = false
local lastPlayerAddress = nil
local CharacterBaseAttributeSetClass = nil

local function safeIsValid(obj)
    if obj == nil then
        return false
    end

    local ok, valid = pcall(function()
        return obj:IsValid()
    end)

    return ok and valid == true
end

local function loadCount()
    local file = io.open(COUNTER_PATH, "r")
    if not file then
        return 0
    end

    local text = file:read("*a") or ""
    file:close()

    return tonumber(text:match("(%d+)")) or 0
end

local function writeCount()
    local file = io.open(COUNTER_PATH, "w")
    if not file then
        print("[DawnwalkerDeathCounter] Nie moge zapisac: " .. COUNTER_PATH)
        return
    end

    file:write(string.format("ZGONY: %d", count))
    file:close()
end

local function getCharacterBaseAttributeSetClass()
    if safeIsValid(CharacterBaseAttributeSetClass) then
        return CharacterBaseAttributeSetClass
    end

    local ok, classObject = pcall(function()
        return StaticFindObject("/Script/DogwoodStats.CharacterBaseAttributeSet")
    end)

    if ok and classObject ~= nil then
        CharacterBaseAttributeSetClass = classObject
        return CharacterBaseAttributeSetClass
    end

    return nil
end

local function getPlayerHealth(player)
    local okAsc, asc = pcall(function()
        return player.AbilitySystemComponent
    end)

    if not okAsc or not safeIsValid(asc) then
        return nil
    end

    local attributeSetClass = getCharacterBaseAttributeSetClass()
    if attributeSetClass == nil then
        return nil
    end

    local okSet, attributeSet = pcall(function()
        return asc:GetAttributeSet(attributeSetClass)
    end)

    if not okSet or not safeIsValid(attributeSet) then
        return nil
    end

    local okHealth, health = pcall(function()
        return attributeSet.Health.CurrentValue
    end)

    if okHealth and type(health) == "number" then
        return health
    end

    return nil
end

local function tickCounter()
    local okPlayer, player = pcall(UEHelpers.GetPlayer)
    if not okPlayer or not safeIsValid(player) then
        return
    end

    local okAddress, playerAddress = pcall(function()
        return player:GetAddress()
    end)

    if okAddress and playerAddress ~= lastPlayerAddress then
        lastPlayerAddress = playerAddress
        wasAlive = false
        deathLatched = false
    end

    local health = getPlayerHealth(player)
    if health == nil then
        return
    end

    if health > DEAD_THRESHOLD then
        wasAlive = true
        deathLatched = false
        return
    end

    if wasAlive and not deathLatched then
        count = count + 1
        deathLatched = true
        writeCount()
        print("[DawnwalkerDeathCounter] Wykryto zgon. Licznik: " .. tostring(count))
    end
end

count = loadCount()
writeCount()
print("[DawnwalkerDeathCounter] Zaladowano. Licznik: " .. tostring(count))

LoopAsync(POLL_MS, function()
    ExecuteInGameThread(function()
        local ok, err = pcall(tickCounter)
        if not ok then
            print("[DawnwalkerDeathCounter] Blad tick: " .. tostring(err))
        end
    end)

    return false
end)

RegisterConsoleCommandHandler("deathcounter_add", function()
    count = count + 1
    writeCount()
    print("[DawnwalkerDeathCounter] Test +1. Licznik: " .. tostring(count))
    return true
end)

RegisterConsoleCommandHandler("deathcounter_reset", function()
    count = 0
    wasAlive = false
    deathLatched = false
    writeCount()
    print("[DawnwalkerDeathCounter] Licznik wyzerowany")
    return true
end)
