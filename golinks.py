from functools import cached_property
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlparse
import json

host_name = "localhost"
port = 6060

LINKS = {
    "youtube": "https://www.youtube.com"
}

@dataclass
class HttpResponse:
    http_code: int
    header: tuple[str, str]
    body: str

@dataclass
class HttpRequest:
    path: str
    query: dict[str, str]



class WebRequestHandler(BaseHTTPRequestHandler):

    @cached_property
    def routes(self):
        return {
            '/go': self.redirect,
            '/list': self.list_links
        }


    @cached_property
    def url(self):
        return urlparse(self.path)

    @cached_property
    def query_data(self):
        return dict(parse_qsl(self.url.query))

    @cached_property
    def http_request(self):
        return HttpRequest(
            self.url.path,
            dict(parse_qsl(self.url.query))
        )


    def do_GET(self):
        request = self.http_request
        print(f"request: {request}")

        response = self.routes[request.path](request)

        self.send_response(response.http_code)
        self.send_header(response.header[0], response.header[1])
        self.end_headers()
        self.wfile.write(response.body.encode("utf-8"))


    def redirect(self, req: HttpRequest) -> HttpResponse:
        tokens = req.query['q'].split(" ")
        link = tokens[0]
        location = LINKS[link]
        header = "Location", location
        response = HttpResponse(302, header, '')
        print(f"redirecting to {response}")
        return response

    def list_links(self, req: HttpRequest) -> HttpResponse:
        header = "ContentType", "application/json"
        body = json.dumps(LINKS)
        response = HttpResponse(200, header, body)
        return response



if __name__ == "__main__":
    web_server = HTTPServer((host_name, port), WebRequestHandler)
    print(f"Server started http:/{host_name}:{port}")

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass

    web_server.server_close()
    print("Server stopped")
