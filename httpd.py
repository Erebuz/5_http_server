import os

from src.server_base_event import EventBaseServer

if __name__ == "__main__":
    server = EventBaseServer(root=os.path.dirname(__file__))

    try:
        server.run()
    except KeyboardInterrupt:
        server.stop()
        print("Interrupted")
