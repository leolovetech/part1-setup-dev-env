import chainlit.data as cl_data
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.data.storage_clients.azure import AzureStorageClient
from dotenv import load_dotenv
import chainlit as cl
import os
load_dotenv()
from openai import AsyncOpenAI

storage_client = AzureStorageClient(account_url=os.getenv("AZURE_STORAGE_URL"), container=os.getenv("AZURE_STORAGE_CONTAINER_NAME"), credential=os.getenv("AZURE_STORAGE_KEY"))
cl_data._data_layer = SQLAlchemyDataLayer(conninfo=os.getenv("SQLALCHEMY_CONNECTION_STRING"), storage_provider=storage_client)
client = AsyncOpenAI()

# Instrument the OpenAI client
# cl.instrument_openai()

settings = {
    "model": "gpt-4o",
    "temperature": 0.7,
    
}

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Fetch the user matching username from your database
    # and compare the hashed password with the value stored in the database
    if (username, password) == ("admin", "admin"):
        return cl.User(
            identifier="admin", metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        return None


#start when loaded chat
@cl.on_chat_start
async def start():
    # AG_Helper(cl.user_session.get("chat_profile"), cl.user_session.get("chat_settings"))
    assert cl_data._data_layer is not None, "Data layer is not set"

@cl.on_message
async def on_message(message: cl.Message):
    response = await client.chat.completions.create(
        messages=[
            {
                "content": "You are a helpful bot",
                "role": "system"
            },
            {
                "content": message.content,
                "role": "user"
            }
        ],
        stream=True,
        **settings
    )
    ai_message = await cl.Message(content="").send()
    async for chunk in response:
        await ai_message.stream_token(chunk.choices[0].delta.content if chunk.choices[0].delta.content is not None else "")
    await ai_message.update()

@cl.on_chat_resume
async def on_chat_resume():
    pass

@cl.on_chat_end
async def on_chat_end():
    pass

@cl.on_stop
async def on_stop():
    pass
