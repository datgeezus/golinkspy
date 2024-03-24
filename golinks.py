from functools import cached_property
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlparse
import json
import argparse

HOST_NAME = "localhost"
PORT = 6060
SEARCH_URL = "https://www.google.com/search?q={}"

@dataclass
class HttpResponse:
    http_code: int
    header: tuple[str, str]
    body: str | None = None

@dataclass
class HttpRequest:
    path: str
    query: dict[str, str]



class WebRequestHandler(BaseHTTPRequestHandler):

    @cached_property
    def routes(self):
        return {
            '/go': self.redirect,
            '/list': self.list_links,
            '/add': self.add_link,
        }

    @cached_property
    def links(self):
        with open('links.json') as f:
            return json.load(f)

    @cached_property
    def search_link(self):
        return self.links.get('_search', SEARCH_URL)


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
            self.query_data
        )


    def do_GET(self):
        request = self.http_request
        print(f"request: {request}")

        response = self.routes[request.path](request)

        self.send_response(response.http_code)
        if response.header:
            self.send_header(response.header[0], response.header[1])
        self.end_headers()
        if response.body:
            self.wfile.write(response.body.encode("utf-8"))


    def redirect(self, req: HttpRequest) -> HttpResponse:
        tokens = req.query['q'].split(" ")
        print(f'tokens {tokens}')
        location = self.__parse_link(tokens)
        header = "Location", location
        response = HttpResponse(302, header)
        print(f"redirecting to {response}")
        return response

    def __parse_link(self, tokens: list[str]) -> str:
        key = tokens[0]
        link = self.links.get(key, self.search_link.format(key))
        if isinstance(link, str):
            return link.format(*tokens[1:])
        else:
            return link.get(tokens[1])


    def list_links(self, req: HttpRequest) -> HttpResponse:
        header = "Content-Type", "application/json"
        body = json.dumps(self.links)
        response = HttpResponse(200, header, body)
        return response

    def add_link(self, req: HttpRequest) -> HttpResponse:
        tokens = req.query['q'].split(" ")
        print(f'tokens {tokens}')
        name = tokens[0]
        url = tokens[1]

        self.save(name, url)

        header = "Content-Type", "application/json"
        body = json.dumps(self.links)
        return HttpResponse(201, header, body)

    def save(self, name: str, url: str):
        self.links[name] = url
        with open('links.json', 'w') as f:
            json.dump(self.links, f, indent=4)
        self.__dict__.pop('links', None)




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", action="store", type=str, default=HOST_NAME)
    parser.add_argument("--port", action="store", type=int, default=PORT)
    args = parser.parse_args()

    host = args.host;
    port = args.port;


    web_server = HTTPServer((host, port), WebRequestHandler)
    print(f"Server started http://{host}:{port}")

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass

    web_server.server_close()
    print("Server stopped")
