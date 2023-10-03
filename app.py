from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()


@app.post('/webhook')
async def webhook(request: Request):
    data = await request.body()
    message = data.get("message")
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    print(f"Message from {chat_id}: {text}")
    return {"status": "200"}


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


if __name__ == '__main__':
    uvicorn.run(app, host="localhost", port=8000)