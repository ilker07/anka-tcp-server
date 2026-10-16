from flask import Flask, request, jsonify
import os

app = Flask(__name__)

veriler = {}
komutlar = {}

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Pico → Sunucu (veri gönder + komut al)
@app.route('/veri/<id>', methods=['POST'])
def veri_al(id):
    gelen_veri = request.get_json(force=True, silent=True) or {}
    veriler[id] = gelen_veri
    aktif_komut = komutlar.pop(id, {"role": gelen_veri.get("role", 0)})
    return jsonify(aktif_komut), 200

# HTML → Sunucu (veriyi oku)
@app.route('/veri/<id>', methods=['GET'])
def veri_gonder(id):
    return jsonify(veriler.get(id, {"ntc": "--", "role": 0})), 200

# HTML → Sunucu (komut yaz)
@app.route('/komut/<id>', methods=['POST'])
def komut_ekle(id):
    gelen_komut = request.get_json(silent=True) or {}
    komutlar[id] = gelen_komut
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
