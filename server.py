#
# ---- Polymarket WS ----


def on_open(ws):
global tracked_tokens
tracked_tokens = fetch_btc_hourly_markets()


sub = {
"type": "market",
"assets_ids": list(tracked_tokens.values())
}
ws.send(json.dumps(sub))
print("Subscribed to Polymarket markets")


def on_message(ws, message):
data = json.loads(message)


if data.get("type") == "book":
asset = data["asset_id"]
bids = data.get("bids", [])
asks = data.get("asks", [])


if asset not in prices:
prices[asset] = {"buy": None, "sell": None, "history": []}


if bids:
prices[asset]["buy"] = bids[0]["price"]
if asks:
prices[asset]["sell"] = asks[0]["price"]


if prices[asset]["buy"] and prices[asset]["sell"]:
mid = (float(prices[asset]["buy"]) + float(prices[asset]["sell"])) / 2
prices[asset]["history"].append(mid)


broadcast_prices()


def start_polymarket_ws():
ws = websocket.WebSocketApp(
"wss://ws-subscriptions-clob.polymarket.com/ws/market",
on_open=on_open,
on_message=on_message
)
ws.run_forever()


# ---- Web Server ----


@app.get("/")
def home():
return HTMLResponse(open("dashboard.html").read())


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
await ws.accept()
clients.add(ws)


try:
while True:
await ws.receive_text()
except:
clients.remove(ws)


def broadcast_prices():
payload = {
"prices": prices,
"labels": tracked_tokens
}
data = json.dumps(payload)


for ws in list(clients):
try:
ws.send_text(data)
except:
clients.remove(ws)


threading.Thread(target=start_polymarket_ws, daemon=True).start()