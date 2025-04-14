

# Actions
INCOME = "I"
FOREIGN_AID = "F"
COUP = "C"
TAX = "T"
ASSASSINATE = "A"
STEAL = "S"
EXCHANGE = "X"
ACTIONS = (INCOME, FOREIGN_AID, COUP, TAX, ASSASSINATE, STEAL, EXCHANGE)
TARGET_ACTIONS = (COUP, ASSASSINATE, STEAL)

# Characters
ASSASSIN = "A"
AMBASSADOR = "B"
CAPTAIN = "C"
DUKE = "D"
CONTESSA = "E"
CHARACTERS = (DUKE, ASSASSIN, CONTESSA, CAPTAIN, AMBASSADOR)

MIN_PLAYERS = 2
MAX_PLAYERS = 6
STARTING_COINS = 2
MAX_COIN_STEAL = 2
INCOME_COINS = 1
FOREIGN_AID_COINS = 2
TAX_COINS = 3
ASSASSINATION_COST = 3
COUP_COST = 7
COUP_COINS_THRESHOLD = 10