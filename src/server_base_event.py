import asyncio
import mimetypes
from asyncio import Server
from email.utils import formatdate
from pathlib import Path
from urllib.parse import unquote_plus

HTTP_BODY_TERMINATOR = "\r\n\r\n"
HTTP_HEADER_TERMINATOR = "\r\n"


class EventBaseServer:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 80,
        root: str = "",
        public_root: str = "./www",
    ) -> None:
        self.HOST = host
        self.PORT = port
        self.root = Path(root)
        self.DOCUMENT_ROOT = self.root / Path(public_root)
        self.server: Server | None = None
        self.server_creator = asyncio.start_server(
            self.handle_client,
            self.HOST,
            self.PORT,
            reuse_address=True,
        )

        self.SERVER_HEADER = "BaseEventServer"

    def run(self) -> None:
        asyncio.run(self._run())

    async def _run(self) -> None:
        if self.server is None:
            self.server = await self.server_creator

        async with self.server:
            print(f"Server started for {self.HOST}:{self.PORT}")
            await self.server.serve_forever()

    def stop(self) -> None:
        if self.server:
            self.server.close()
            print("Server stopped")

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            await self.process_request(reader, writer)
        except Exception as e:
            print("Exception", e)
        finally:
            writer.close()
            await writer.wait_closed()

    async def process_request(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        request = b""
        while not request.endswith(HTTP_BODY_TERMINATOR.encode()):
            message_chunk = await reader.read(1024)

            if not message_chunk:
                return

            request += message_chunk

        request_str = request.decode("utf-8")

        headers = request_str.split(HTTP_HEADER_TERMINATOR)
        method, path_str, _ = headers[0].split()
        # request_headers = {
        #     msg.split(": ")[0]: msg.split(": ")[1] for msg in headers[1:] if msg
        # }

        path_args = path_str.split("?")

        path = path_args[0]
        # args = ""
        # if len(path_args) > 1:
        #     args = path_args[1].split("&")

        self.request_router(method, unquote_plus(path), writer)

        await writer.drain()

    def request_router(
        self, method: str, path: str, writer: asyncio.StreamWriter
    ) -> None:
        if method not in ["GET", "HEAD"]:
            msg = self.get_error_response(405, "Method Not Allowed")

            writer.write(msg.encode("utf-8"))
            return

        if path.endswith("/"):
            path += "index.html"

        file_path = self.DOCUMENT_ROOT / path.lstrip("/")

        if file_path.exists():
            self.write_file_to_writer(file_path, writer, method == "HEAD")
        else:
            msg = self.get_error_response(404, "Not Found")
            writer.write(msg.encode("utf-8"))

    def get_error_response(self, error_code: int, error_msg: str) -> str:
        response = "HTTP/1.1 " + str(error_code) + " " + error_msg + "\r\n"
        headers = {
            "Date": formatdate(timeval=None, localtime=False, usegmt=True),
            "Server": self.SERVER_HEADER,
            "Content-Type": "text/plain; charset=utf-8",
            "Content-Length": len(error_msg),
            "Connection": "keep-alive",
        }
        response += HTTP_HEADER_TERMINATOR.join(
            [": ".join([k, str(v)]) for k, v in headers.items()]
        )
        response += HTTP_BODY_TERMINATOR
        return response + error_msg

    def write_file_to_writer(
        self, file_path: Path, writer: asyncio.StreamWriter, empty_response: bool = True
    ) -> None:
        headers = {
            "Date": formatdate(timeval=None, localtime=False, usegmt=True),
            "Server": self.SERVER_HEADER,
            "Content-Type": self.get_content_type(file_path),
            "Content-Length": file_path.stat().st_size,
            "Connection": "keep-alive",
        }

        headers_str = "HTTP/1.1 200 OK\r\n"
        headers_str += HTTP_HEADER_TERMINATOR.join(
            [": ".join([k, str(v)]) for k, v in headers.items()]
        )
        headers_str += HTTP_BODY_TERMINATOR

        writer.write(headers_str.encode("utf-8"))

        if not empty_response:
            with open(file_path, "rb") as f:
                while chunk := f.read(1024):
                    writer.write(chunk)

    @staticmethod
    def get_content_type(file_path: Path) -> str:
        mime_type, _ = mimetypes.guess_type(file_path)

        if not mime_type:
            return "application/octet-stream"

        # text_types = ["text/html", "text/css", "application/javascript", "text/plain"]
        # if mime_type in text_types or mime_type.startswith("text/"):
        #     return f"{mime_type}; charset=utf-8"

        return mime_type
