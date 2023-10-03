from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()


@app.post('/webhook')
async def webhook(request: Request):
    body = await request.body()
    print(body)
    return {"status": "200"}


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


if __name__ == '__main__':
    uvicorn.run(app, host="localhost", port=8000)