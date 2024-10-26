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
Each game of Coup is simulated and played using a **Server**, a **Root** and 2-5 **Clients**. The connections between these hodes are as follows:



<div style="text-align: center;">
<img src="network_diagram.png" alt="Alt text" width="300"/>
</div>

### Server
The **Server** is responsible for routing the messages between each **Client** and the **Root**.

### Client
The **Clients** are instances controlled by the players. The purpose of this project is to implement several instances of a bot player, each one running on a different **Client**.

### Root
The **Root** is the central node that holds the game state and is responsible for updating the game state based on the actions taken by the **Clients**. This node validates each **Client**'s move according to the possible moves and replies messages to be broadcasted or addressed to a specific **Client**. The **Root** is, to the **Server**, also seen as a **Client** but since it's always the first one to connect, its ID is always 0.

### Communication
Each message sent by a **Client** is always routed to the **Root**. The **Root** then decides whether to invalidate the message, to broadcast it to the other **Clients** or to simply update the game state.

### Instancing
1. To instanciate the **Root** and the **Server**, run `python src/run_server.py`. This will start the server and spawn an instance of the **Root** that connects automatically to the **Server** using the same address and port.

2. To instanciate one **Client** as a player, there are 2 options:
- run `python src/run_bot.py` to connect to the **Server** as a bot.
- run `python src/run_human.py` to connect to the **Server** as a human. This allows to test sending commands manually.

Each instance must run on a separate terminal, but not necessarily on the same machine. As long as the connection address and port matches the **Server**, **Clients** can connect from different machines.

## Bot implementation
To implement a bot, you must edit or duplicate the `CoupBot` class and implement the `receive()` method. This class must be inside the `src/client/bots.py` file. If you choose to duplicate the `CoupBot` class once or more (perhaps to test different bots yourself), remember to import and change the class used by `run_bot.py` to run your desired bot. If you don't do this, the `CoupBot` class will be used by default.

The `receive()` method will be called whenever the bot receives a new message. Here, the bot can update its state/knowledge with the information from the message and *may or may not* put a reply message on its checkout queue to send to the **Root**, depending on the received message.


## Message Protocol
The messages exchanged between the **Root** and the **Clients** are strings with a specific format. 

Some messages start with `command|ID1` where `ID1` is the origin **Client** ID which is a number automatically assigned by the **Server** when first connecting. Messages without any ID are reserved for private communication between the **Root** and each **Client**, which means that these messages will never be broadcasted from one **Client** to another. 

Below is the full list of the accepted Protocol messages.

**This list is subject to change with addition of more commands!**

| Command | Description |
|---------|-------------|
| `ACT\|ID1\|ACTION\|ID2`    | Player Action: `ID1` = Player ID, `ACTION` = Action type, `ID2` = Target Player ID (if applicable) |
| `OK`                       | Allow Action/Block or acknowledge information |
| `BLOCK\|ID1\|card`         | Block Action: `ID1` = Player ID blocking an action, `card` = Character used to block |
| `CHAL\|ID1`                | Challenge Action: `ID1` = Player ID challenging an action or block |
| `SHOW`                     | Request Card Reveal from a player |
| `SHOW\|ID1\|card`          | Player Card Reveal: `ID1` = Player ID, `card` = Character card to reveal |
| `LOSE`                     | Request for a Player to Lose Influence |
| `LOSE\|ID1\|card`          | Lose Influence: `ID1` = Player ID, `card` = Character card lost |
| `COINS\|ID1\|coins`        | Update Coins: `ID1` = Player ID, `coins` = Current coin count |
| `DECK\|card1\|card2`       | Inform Player of Current Deck: `card1` = First card, `card2` = Second card (available depending on the game state) |
| `CHOOSE\|card1\|card2`     | Ask Player to Choose Cards to Exchange: `card1` = First choice, `card2` = Second choice (available depending on the game state) |
| `KEEP\|card1\|card2`       | Player Chooses Which 2 Cards to Keep: `card1` = First card to keep, `card2` = Second card to keep (available depending on the game state) |
| `HELLO`                    | Register on the Root to obtain ID |
| `PLAYER\|ID1`              | Broadcast ID of a registered player: `ID1` = Registered player ID |
| `START`                    | Sync all players to start game. |
| `TURN\|ID1`                | Ask a player for an action: `ID1` = Player ID |
| `EXIT`                     | Remove player from game |
| `ILLEGAL`                  | Player made an illegal move |

## Message origins and reply limitations

These are all possible messages each **Client** can receive and all possible replies:
| Receive | Reply |
|---------|-------|
| `ACT\|ID1\|ACTION\|ID2` | `OK`, `CHAL\|ID1`, `BLOCK\|ID1\|card` |
| `BLOCK\|ID1\|card` | `OK`, `CHAL\|ID1` |
| `CHAL\|ID1` | None |
| `SHOW` | `SHOW\|ID1\|card` |
| `SHOW\|ID1\|card` | `OK` |
| `LOSE` | `LOSE\|ID1\|card` |
| `LOSE\|ID1\|card` | `OK` |
| `COINS\|ID1\|coins` | `OK` |
| `DECK\|card1\|card2` | `OK` |
| `CHOOSE\|card1\|card2` | `KEEP\|card1\|card2` |
| `PLAYER\|ID1` | `OK` |
| `START` | `OK` |
| `TURN\|ID1` | `OK`, `ACT\|ID1\|ACTION\|ID2` |
| `EXIT` | None |
| `ILLEGAL` | ** |

\* The **Client** should reply `OK` if ID1 is not its own ID.

\** If a player receives `ILLEGAL`, it means that the previously sent message was either not needed or wrong. The player must reevaluate what to send. If the player sends 2 illegal messages in a row, the **Root** replies with `END|ID` and the player is kicked from the game.


## Game initialization
To startup the game, there is a sequence of commands that must be used to initialize the players. First, the server starts. Then, all clients can connect.


0.  Root starts
1.  Player connects 
2.  Player ---> Root: `HELLO`
3.  Player <--- Root: `PLAYER|ID1`
4.  Player ---> Root: `OK`
5.  Player <--- Root: `START` (this command is sent manually)
6.  Player ---> Root: `OK`
7.  Player <--- Root: `DECK|card1|card2`
8.  Player ---> Root: `OK`
9.  Player <--- Root: `COINS|ID1|coins`
10. Player ---> Root: `OK`
11. Player <--- Root: `PLAYER|ID2`
12. Player ---> Root: `OK`
13. Player <--- Root: `PLAYER|ID3`
14. Player ---> Root: `OK`
15. Player <--- Root: `PLAYER|ID4`
16. Player ---> Root: `OK`
17. Player <--- Root: `PLAYER|ID5`
18. Player ---> Root: `OK`
19. Player <--- Root: `TURN|ID`

## Challenge resolution
### Scenario 1: P1 challenges P2's action and P2 loses
#### P1
1. Player ---> Root: `CHAL|P1`
2. Player <--- Root: `LOSE|P2|card`
3. Player ---> Root: `OK`

#### P2
1. Player <--- Root: `CHAL|P1`
2. Player ---> Root: `LOSE|P2|card`

#### other players
1. Player <--- Root: `CHAL|P1`
2. Player ---> Root: `OK`
3. Player <--- Root: `LOSE|P2|card`
4. Player ---> Root: `OK`


### Scenario 2: P1 challenges P2's action and P2 wins
#### P1
1. Player ---> Root: `CHAL|P1`
2. Player <--- Root: `SHOW|P2|card`
3. Player ---> Root: `LOSE|P1|card`

#### P2
1. Player <--- Root: `CHAL|P1`
2. Player ---> Root: `SHOW|P2|card`
3. Player <--- Root: `LOSE|P1|card`
4. Player ---> Root: `OK`

#### other players
1. Player <--- Root: `CHAL|P1`
2. Player ---> Root: `OK`
3. Player <--- Root: `SHOW|P2|card`
4. Player ---> Root: `OK`
5. Player <--- Root: `LOSE|P1|card`
6. Player ---> Root: `OK`

## Exchange resolution
### Scenario: P1 plays an exchange move
#### P1
1. Player <--- Root: `TURN|P1`
2. Player ---> Root: `ACT|P1|X`
3. Player <--- Root: `CHOOSE|card3|card4`
4. Player ---> Root: `KEEP|card2|card4`

#### other players
1. Player <--- Root: `TURN|P1`
2. Player ---> Root: `OK`
3. Player <--- Root: `ACT|P1|X`
4. Player ---> Root: `OK`
