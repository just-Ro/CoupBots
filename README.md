# CoupBots
Crazy attempt to have bots play coup together.


<div style="text-align: center;">
<img src="https://cf.geekdo-images.com/MWhSY_GOe2-bmlQ2rntSVg__itemrep/img/QRw3T5XGsrRs-QKCSpzwE7nFqOg=/fit-in/246x300/filters:strip_icc()/pic2016054.jpg" alt="Alt text" width="200"/>
</div>

## Objective
This project serves as a programming championship to determine which bot is the best overall. The winning bot must win, on average, more games than the rest of the bots.


## Game Rules
The original rules of Coup can be read [here](https://www.qugs.org/rules/r131357.pdf).

## Network arrangement
Each game of Coup is simulated and played using a **Server**, a **Root Node** and 2-5 **Clients**. The connections between these hodes are as follows:



<div style="text-align: center;">
<img src="guide/network_diagram.png" alt="Alt text" width="300"/>
</div>

### Server
The **Server** is responsible for routing the messages between each **Client** and the **Root Node**.

### Client
The **Clients** are instances controlled by the players. The purpose of this project is to implement several instances of a bot player, each one running on a different **Client**.

### Root Node
The **Root Node** is the central node that holds the game state and is responsible for updating the game state based on the actions taken by the **Clients**. This node validates each **Client**'s move according to the possible moves and replies messages to be broadcasted or addressed to a specific **Client**. The **Root Node** is, to the **Server**, also seen as a **Client** but since it's always the first one to connect, its ID is always 0.

### Communication
Each message sent by a **Client** is always routed to the **Root Node**. The **Root Node** then decides whether to invalidate the message, to broadcast it to the other **Clients** or to simply update the game state.

### Instancing
1. To instanciate the **Root Node** and the **Server**, run `python src/run_server.py`. This will start the server and spawn an instance of the **Root Node** that connects automatically to the **Server** using the same address and port.

2. To instanciate one **Client** as a player, there are 2 options:
- run `python src/run_bot.py` to connect to the **Server** as a bot.
- run `python src/run_human.py` to connect to the **Server** as a human. This allows to test sending commands manually.

Each instance must run on a separate terminal, but not necessarily on the same machine. As long as the connection address and port matches the **Server**, **Clients** can connect from different machines.

## Bot implementation
To implement a bot, you must edit or duplicate the `CoupBot` class and implement the `receive()` method. This class must be inside the `src/client/bots.py` file. If you choose to duplicate the `CoupBot` class once or more (perhaps to test different bots yourself), remember to import and change the class used by `run_bot.py` to run your desired bot. If you don't do this, the `CoupBot` class will be used by default.

The `receive()` method will be called whenever the bot receives a new message. Here, the bot can update its state/knowledge with the information from the message and *may or may not* put a reply message on its checkout queue to send to the **Root Node**, depending on the received message.


## Message Protocol
The messages exchanged between the **Root Node** and the **Clients** are strings with a specific format. 

Some messages start with `command|ID1` where `ID1` is the origin **Client** ID which is a number automatically assigned by the **Server** when first connecting. Messages without any ID are reserved for private communication between the **Root Node** and each **Client**, which means that these messages will never be broadcasted from one **Client** to another. 

Below is the full list of the accepted Protocol messages.

**This list is subject to change with addition of more commands!**

| Command | Description |
|---------|-------------|
| `ACT\|ID1\|ACTION\|ID2`    | Player Action: `ID1` = Player ID, `ACTION` = Action type, `ID2` = Target Player ID (if applicable) |
| `ALLOW\|ID1`               | Allow Action: `ID1` = Player ID allowing an action to proceed (no block, no challenge) |
| `CHAL\|ID1`                | Challenge Action: `ID1` = Player ID challenging an action or block |
| `BLOCK\|ID1\|card`         | Block Action: `ID1` = Player ID blocking an action, `card` = Character used to block |
| `SHOW`                     | Request Card Reveal from a player |
| `SHOW\|ID1\|card`          | Player Card Reveal: `ID1` = Player ID, `card` = Character card to reveal |
| `LOSE`                     | Request for a Player to Lose Influence |
| `LOSE\|ID1\|card`          | Lose Influence: `ID1` = Player ID, `card` = Character card lost |
| `COINS\|ID1\|coins`        | Update Coins: `ID1` = Player ID, `coins` = Current coin count |
| `DECK\|card1\|card2`       | Inform Player of Current Deck: `card1` = First card, `card2` = Second card (available depending on the game state) |
| `CHOOSE\|card1\|card2`     | Ask Player to Choose Cards to Exchange: `card1` = First choice, `card2` = Second choice (available depending on the game state) |
| `KEEP\|card1\|card2`       | Player Chooses Which 2 Cards to Keep: `card1` = First card to keep, `card2` = Second card to keep (available depending on the game state) |
| `HELLO`                    | Register on the Root Node to obtain ID |
| `PLAYER\|ID1`              | Broadcast ID of a registered player: `ID1` = Registered player ID |
| `START`                    | Sync all players to start game. |
| `READY`                    | Player Ready |
| `TURN\|ID1`                | Ask a player for an action: `ID1` = Player ID |
| `END\|ID1`                 | Remove player from game: `ID1` = Player ID |
| `WIN\|ID1`                 | Player wins the game: `ID1` = Player ID |
| `ILLEGAL`                  | Player made an illegal move |

## Message origins and reply limitations

### **Client** can receive from **Root Node**:
| Receive | Reply |
|---------|-------|
| `CHOOSE\|card1\|card2` | `KEEP\|card1\|card2` |
| `TURN\|ID1` | `ACT\|ID1\|ACTION\|ID2` * |
| `SHOW` | `SHOW\|ID1\|card` |
| `LOSE` | `LOSE\|ID1\|card` |
| `START` | `READY` |
| `PLAYER\|ID1` | None |
| `DECK\|card1\|card2` | None |
| `COINS\|ID1\|coins` | None |
| `END\|ID1` | None |
| `WIN\|ID1` | None |
| `ILLEGAL` | ** |

\* The **Client** should only reply to these commands if `ID1` is its own ID.

\** If a player receives `ILLEGAL`, it means that the previously sent message was either not needed or wrong. The player must reevaluate what to send. If the player sends 2 illegal messages in a row, the **Root Node** replies with `END|ID` and the player is kicked from the game.

### **Client** can send to **Root Node**:
| Send |
|------|
| `HELLO` |
| `READY` |
| `KEEP\|card1\|card2` |

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
1. Player connects 
2. Root <- Player: `HELLO`
3. Root -> Player: `PLAYER|ID1`
4. Root -> Player: `START` (this command is sent manually)
5. Root <- Player: `READY`
6. Root -> Player: `DECK|card1|card2`
7. Root -> Player: `COINS|ID1|coins`
8. Root -> Player: `PLAYER|ID1`, `PLAYER|ID1`, ...
9. Root -> Player: `TURN|ID1`
