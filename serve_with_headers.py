from http.server import HTTPServer, SimpleHTTPRequestHandler
import sys, os

class COEPHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Required headers for cross-origin WASM/CORP resources
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        SimpleHTTPRequestHandler.end_headers(self)

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    webroot = os.path.join(os.path.dirname(__file__), 'build', 'web')
    if os.path.isdir(webroot):
        os.chdir(webroot)
    else:
        print('build/web not found; run python -m pygbag --build . first')
        sys.exit(1)
    server = HTTPServer(('0.0.0.0', port), COEPHandler)
    print(f'Serving {os.getcwd()} on port {port} with COEP/COOP headers')
    server.serve_forever()
