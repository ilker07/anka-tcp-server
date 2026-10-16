import socket
import threading
import json
import os

HOST = '0.0.0.0'
PORT = int(os.environ.get('PORT', 10000))

veriler = {}
komutlar = {}
clients = {}

def handle_client(conn, addr):
    print(f"Bağlandı: {addr}")
    cihaz_id = None
    buf = ""
    
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            buf += data.decode("utf-8", "replace")
            
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                
                try:
                    msg = json.loads(line)
                    cihaz_id = str(msg.get("id", addr[0]))
                    clients[cihaz_id] = conn
                    
                    # Veriyi kaydet
                    veriler[cihaz_id] = msg
                    
                    # Komut var mı?
                    komut = komutlar.pop(cihaz_id, {})
                    
                    # Cevap gönder
                    cevap = json.dumps(komut) + "\n"
                    conn.sendall(cevap.encode())
                    
                except Exception as e:
                    print("Parse hatası:", e)
    
    except Exception as e:
        print(f"Client hatası {addr}:", e)
    finally:
        if cihaz_id and cihaz_id in clients:
            del clients[cihaz_id]
        conn.close()
        print(f"Bağlantı kapandı: {addr}")


def start_http(port):
    """HTML için basit HTTP sunucusu — aynı process içinde"""
    import http.server
    import urllib.parse

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # log kapat

        def do_GET(self):
            path = urllib.parse.urlparse(self.path).path
            parts = path.strip("/").split("/")

            if len(parts) == 2 and parts[0] == "veri":
                cid = parts[1]
                data = json.dumps(veriler.get(cid, {"ntc": "--", "role": 0}))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(data.encode())
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            path = urllib.parse.urlparse(self.path).path
            parts = path.strip("/").split("/")
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)

            if len(parts) == 2 and parts[0] == "komut":
                cid = parts[1]
                try:
                    komutlar[cid] = json.loads(body)
                except:
                    pass
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(b"OK")
            else:
                self.send_response(404)
                self.end_headers()

        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

    http_port = port + 1
    server = http.server.HTTPServer(("0.0.0.0", http_port), Handler)
    print(f"HTTP sunucu başladı: {http_port}")
    server.serve_forever()


# HTTP sunucuyu ayrı thread'de başlat
PORT_HTTP = int(os.environ.get('PORT', 10000))
t = threading.Thread(target=start_http, args=(PORT_HTTP,), daemon=True)
t.start()

# TCP sunucu
print(f"TCP sunucu başladı: {PORT}")
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(100)

while True:
    conn, addr = server.accept()
    thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
    thread.start()
