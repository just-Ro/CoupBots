# CoupBots Implementation Guide
## Introduction
Welcome to the CoupBots implementation guide. This guide will walk you through the rules, objectives and implementation details that you need to know before and while developing your bot to play Coup! 

## Bot implementation
To implement a bot, you must edit or duplicate the `CoupBot` class and implement the `update()` and `action()` methods. This class must be inside the `src/client/bots.py` file.

- The `update()` method will be called whenever the bot receives a new message. Here, the bot can update its state/knowledge with the information from the message.
- The `action()` method will be called whenever the bot needs to take an action. Here, the bot *may or may not* return a message to send to the **Root Node**, depending on the message.

If you choose to duplicate the `CoupBot` class once or more (perhaps to test different bots yourself), remember to import and change the class used by `run_bot.py` to run your desired bot. If you don't do this, the `CoupBot` class will be used by default.

### Message Protocol
The messages exchanged between the **Root Node** and the **Clients** are strings with a specific format. All messages start with `command|ID` where "ID" is the origin **Client** ID which is a number automatically assigned by the **Server**. Below is the full list of the accepted Protocol messages.

| Command                   | Description                                                                                 |
|---------------------------|---------------------------------------------------------------------------------------------|
| `INIT\|ID\|card1,card2\|coins`  | Game Initialization: `ID` = Player ID, `card1` = First card, `card2` = Second card, `coins` = Initial coin count |
| `READY\|ID`                | Player Ready: `ID` = Player ID |
| `ACT\|ID\|ACTION\|targetID(optional)` | Player Action: `ID` = Player ID, `ACTION` = Action type, `targetID` = Target Player ID (if applicable) |
| `ALLOW\|ID`                | Allow Action: `ID` = Player ID allowing an action to proceed (no block, no challenge) |
| `CHAL\|ID\|targetID\|ACTION` | Challenge Action: `ID` = Challenger Player ID, `targetID` = Player performing action, `ACTION` = Action being challenged |
| `BLOCK\|ID\|ACTION\|card`    | Block Action: `ID` = Blocking Player ID, `ACTION` = Action being blocked, `card` = Character used to block |
| `SHOW\|ID\|card`            | Request Card Reveal: `ID` = Player ID, `card` = Character card to reveal |
| `LOSE\|ID\|card`            | Lose Influence: `ID` = Player ID, `card` = Character card lost |
| `COINS\|ID\|coins`         | Update Coins: `ID` = Player ID, `coins` = Current coin count |
| `END\|ID`                 | Game End: `ID` = Player ID of the winner |
| `DECK\|ID\|card1\|card2`     | Inform Player of Current Deck: `ID` = Player ID, `card1` = First card, `card2` = Second card |
| `CHOOSE\|ID\|card1\|card2`   | Ask Player to Choose Cards to Exchange: `ID` = Player ID, `card1` = First card to choose, `card2` = Second card to choose |
| `KEEP\|ID\|card1\|card2`     | Player Chooses Which 2 Cards to Keep: `ID` = Player ID, `card1` = First card to keep, `card2` = Second card to keep |

