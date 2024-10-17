# CoupBots Implementation Guide
## Introduction
Welcome to the CoupBots implementation guide. This guide will walk you through the rules, objectives and implementation details that you need to know before and while developing your bot to play Coup! 

## Bot implementation
To implement a bot, you must edit or duplicate the `CoupBot` class and implement the `receive()` method. This class must be inside the `src/client/bots.py` file. If you choose to duplicate the `CoupBot` class once or more (perhaps to test different bots yourself), remember to import and change the class used by `run_bot.py` to run your desired bot. If you don't do this, the `CoupBot` class will be used by default.

The `receive()` method will be called whenever the bot receives a new message. Here, the bot can update its state/knowledge with the information from the message and *may or may not* put a reply message on its checkout queue to send to the **Root Node**, depending on the received message.


## Message Protocol
The messages exchanged between the **Root Node** and the **Clients** are strings with a specific format. Almost all messages start with `command|ID` where "ID" is the origin **Client** ID which is a number automatically assigned by the **Server**. Below is the full list of the accepted Protocol messages. **This list is subject to change with addition of more commands**!

| Command | Description |
|---------|-------------|
| `ACT\|ID1\|ACTION\|ID2` | Player Action: `ID1` = Player ID, `ACTION` = Action type, `ID2` = Target Player ID (if applicable) |
| `ALLOW\|ID1`                | Allow Action: `ID1` = Player ID allowing an action to proceed (no block, no challenge) |
| `CHAL\|ID1`                | Challenge Action: `ID1` = Player ID challenging an action or block |
| `BLOCK\|ID1\|card`         | Block Action: `ID1` = Player ID blocking an action, `card` = Character used to block |
| `SHOW\|ID1\|card`            | Request Card Reveal: `ID1` = Player ID, `card` = Character card to reveal |
| `LOSE\|ID1\|card`            | Lose Influence: `ID1` = Player ID, `card` = Character card lost |
| `COINS\|ID1\|coins`         | Update Coins: `ID1` = Player ID, `coins` = Current coin count |
| `DECK\|ID1\|card1\|card2`     | Inform Player of Current Deck: `ID1` = Player ID, `card1` = First card, `card2` = Second card |
| `CHOOSE\|ID1\|card1\|card2`   | Ask Player to Choose Cards to Exchange: `ID1` = Player ID, `card1` = First choice, `card2` = Second choice |
| `KEEP\|ID1\|card1\|card2`     | Player Chooses Which 2 Cards to Keep: `ID1` = Player ID, `card1` = First card to keep, `card2` = Second card to keep |
| `HELLO` | Register on the Root Node to obtain ID |
| `PLAYER\|ID1` | Broadcast ID of a registered player: `ID1` = Registered player ID |
| `START` | Sync all players to start game. |
| `READY\|ID1`                | Player Ready: `ID1` = Player ID |
| `TURN\|ID1` | Ask a player for an action: `ID1` = Player ID |
| `END\|ID1` | Remove player from game: `ID1` = Player ID |
| `WIN\|ID1` | Player wins the game: `ID1` = Player ID |
| `ILLEGAL\|ID1` | Player made an illegal move: `ID1` = Player ID |

## Message origins and reply limitations

### **Client** can receive from **Root Node**:
| Receive | Reply |
|---------|-------|
| `CHOOSE\|ID1\|card1\|card2` | `KEEP\|ID1\|card1\|card2` |
| `TURN\|ID1` | `ACT\|ID1\|ACTION\|ID2` |
| `SHOW\|ID1` | `SHOW\|ID1\|card` |
| `LOSE\|ID1` | `LOSE\|ID1\|card` |
| `START` | `READY\|ID1` |
| `PLAYER\|ID1` | None |
| `DECK\|ID1\|card1\|card2` | None |
| `COINS\|ID1\|coins` | None |
| `END\|ID1` | None |
| `WIN\|ID1` | None |
| `ILLEGAL\|ID1` | * |

\* If a player receives `ILLEGAL\|ID1`, it means that the previously sent message was either not needed or wrong. The player must reevaluate what to send. If the player sends 2 illegal messages in a row, the **Root Node** replies with `END|ID` and the player is kicked from the game.

### **Client** can send to **Root Node**:
| Send |
|------|
| `HELLO` |
| `READY\|ID1` |
| `KEEP\|ID1\|card1\|card2` |

### **Client** can send and receive (**Client** to **Client**):
| Receive | Reply |
|---------|-------|
| `ACT\|ID1\|ACTION\|ID2` | `ALLOW\|ID1`, `CHAL\|ID1`, `BLOCK\|ID1\|card` |
| `BLOCK\|ID1\|card` | `CHAL\|ID1` |
| `CHAL\|ID1` | None |
| `ALLOW\|ID1` | None |
| `SHOW\|ID1\|card` | None |
| `LOSE\|ID1\|card` | None |

## Game initialization
To startup the game, there is a set of commands that must be used to initialize the players. First, the server starts. Then, all clients can connect.


0. Root starts
1. Player connects and sends `HELLO`
2. Root replies `PLAYER|ID1`
3. Player receives `PLAYER|ID1` with its ID
4. Root sends `START`
5. Player receives `START`
6. Player replies `READY\|ID1`
7. Root replies `DECK|ID1|card1|card2`, `COINS|ID1|coins` and many `PLAYER|ID1`
8. Player receives `DECK|ID1|card1|card2`, `COINS|ID1|coins` and many `PLAYER|ID1` with the other player's IDs
9. Root sends `TURN|ID1`
10. Player receives `TURN|ID1`