# -*- coding: utf-8 -*-
"""b40_9_ornek_yanit.py: Bir hata yanitinin tam govdesini gosterir."""

import json
import threading
from http.server import HTTPServer

import b40_6_ihafilo_api as api
import b40_7_istemci as ist

srv = HTTPServer(("127.0.0.1", 0), api.Istek)
threading.Thread(target=srv.serve_forever, daemon=True).start()
ist.TABAN = "http://127.0.0.1:%d" % srv.server_address[1]

durum, basl, govde = ist.istek(
    "POST", "/ihalar", govde={"ad": "X", "tip": "ucak"}
)
print("HTTP", durum, basl["content-type"])
print(json.dumps(json.loads(govde), indent=2, ensure_ascii=False))
srv.shutdown()
