import socket
import threading
import sys
from loguru import logger


DEFAULT_ADDR = True  # Use default address for messages

class Client:
    def __init__(self, host="localhost", port=12345):
        self.host = host
        self.port = port
        self.socket = None
        self.signal = True

    def sender(self):
        """
        Gets a new message and tries to send it.

        The program ends when this method returns.
        """

        while self.signal:
            try:
                message = input()
                self.send(message)
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt detected, closing connection.")
                self.signal = False
                break

    def receiver(self, message: str):
        """
        Prints a message to the console

        Arguments:
            message {str} -- message that will be printed
        """

        print(message)

    # -- Wrappers --

    def send(self, message: str):
        """
        Sends a message to the server

        Arguments:
            message {str} -- message to be sent
        """

        self.__handle_send__(message)

    def run(self):
        """
        runs the client
        """

        self.__run__()

    # -- Private methods --

    def __handle_send__(self, message: str):
        """
        Sends a message to the server

        Arguments:
            message {str} -- message to be sent
        """

        try:
            if self.socket is not None:
                self.socket.sendall(message.encode("utf-8"))
            else:
                logger.warning("You are not connected to the server.")
                self.signal = False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.signal = False

    def __connect__(self):
        """
        Connects to the server
        """

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            logger.success(f"Connected to server at {self.host}:{self.port}")
            self.socket.settimeout(1)
        except Exception as e:
            logger.error(f"Could not make a connection to the server: {e}")
            sys.exit(0)

    def __handle_receive__(self):
        """
        Continuously receives messages from the server and calls receiver with any new message
        """

        buffer = ""
        while self.signal:
            try:
                if self.socket is not None:
                    data = self.socket.recv(256)
                    if data:
                        buffer += data.decode("utf-8")
                        while "\n" in buffer:
                            message, buffer = buffer.split("\n", 1)
                            self.receiver(message)
                        continue
                logger.error("Server has closed the connection.")
                self.signal = False
                break
            except socket.timeout:
                continue
            except:
                logger.error("You have been disconnected from the server.")
                self.signal = False
                break

    def __start_receiving__(self):
        """
        Starts a thread for receiving messages from the server
        """

        receive_thread = threading.Thread(target=self.__handle_receive__)
        receive_thread.start()

    def __run__(self):
        """
        Initializes the server connection and starts running the client
        """

        self.__connect__()
        self.__start_receiving__()
        self.sender()


if __name__ == "__main__":
    # Get host and port
    if DEFAULT_ADDR:
        print("Using default address for messages.")
        host = "localhost"
        port = 12345
    else:
        host = input("Host (default 'localhost'): ") or "localhost"
        port = input("Port (default '12345'): ") or "12345"
        port = int(port)  # Ensure port is an integer

    # Create and run the client
    client = Client(host, port)
    client.run()
