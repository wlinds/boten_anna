#!/usr/bin/env python3
"""
A quick callback server to capture SoundCloud authorization code, listening on http://localhost:8080/callback
Run this standalone to authorize of your SoundCloud app
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"\nReceived request: {self.path}")
        
        # Parse the URL to get all parameters
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        print(f"📋 All parameters received:")
        for key, value in query_params.items():
            print(f"   {key}: {value[0] if value else 'None'}")
        
        # Look for authorization code in various possible parameter names
        possible_code_params = ['code', 'authorization_code', 'auth_code', 'token']
        auth_code = None
        
        for param_name in possible_code_params:
            if param_name in query_params:
                auth_code = query_params[param_name][0]
                print(f"\nFound authorization code in '{param_name}': {auth_code}")
                break
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        if auth_code:
            response_html = f"""
            <html>
            <head><title>SoundCloud Authorization Success</title></head>
            <body style="font-family: Arial, sans-serif; margin: 40px;">
                <h1 style="color: green;">Authorization Successful!</h1>
                <h2>Your authorization code:</h2>
                <div style="background: #f0f0f0; padding: 15px; border-radius: 5px; font-family: monospace; word-break: break-all;">
                    {auth_code}
                </div>
                <h3>Next step:</h3>
                <p>Use this command in your Telegram bot:</p>
                <code style="background: #e0e0e0; padding: 10px; display: block; margin: 10px 0;">
                    /sc_auth {auth_code}
                </code>
                <p style="color: #666;">You can close this window and stop the server (Ctrl+C in terminal).</p>
            </body>
            </html>
            """
            
            print(f"\nSUCCESS! Use this command in your bot:")
            print(f"   /sc_auth {auth_code}")
            print(f"\nPress Ctrl+C to stop the server.\n")
            
        else:
            response_html = """
            <html>
            <head><title>SoundCloud Authorization</title></head>
            <body style="font-family: Arial, sans-serif; margin: 40px;">
                <h1 style="color: orange;">No Authorization Code Found</h1>
                <p>The request was received but no authorization code was found in the expected parameters.</p>
                <p>Check the terminal output for all received parameters.</p>
            </body>
            </html>
            """
        
        self.wfile.write(response_html.encode())
    
    def log_message(self, format, *args):
        # Suppress default HTTP logging to keep output clean
        pass

def main():
    server_address = ('localhost', 8080)
    httpd = HTTPServer(server_address, CallbackHandler)
    
    print("SoundCloud Callback Server Starting...")
    print("Listening on: http://localhost:8080/callback")
    print("Now visit your SoundCloud authorization URL")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped. Have a great day!")
        httpd.server_close()
        sys.exit(0)

if __name__ == "__main__":
    main()