# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
This sample shows how to create a simple EchoBot with state.
"""


from random import randint
from aiohttp import web
from botbuilder.schema import (Activity, ActivityTypes)
from botbuilder.core import (BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext,
                             ConversationState, MemoryStorage, UserState)

APP_ID = ''
APP_PASSWORD = ''
PORT = 9000
SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)

# Create MemoryStorage, UserState and ConversationState
memory = MemoryStorage()
# Commented out user_state because it's not being used.
# user_state = UserState(memory)
conversation_state = ConversationState(memory)

# Register both State middleware on the adapter.
# Commented out user_state because it's not being used.
# ADAPTER.use(user_state)
ADAPTER.use(conversation_state)


async def create_reply_activity(request_activity, text) -> Activity:
    return Activity(
        type=ActivityTypes.message,
        channel_id=request_activity.channel_id,
        conversation=request_activity.conversation,
        recipient=request_activity.from_property,
        from_property=request_activity.recipient,
        text=text,
        service_url=request_activity.service_url)


async def handle_message(context: TurnContext) -> web.Response:
    # Access the state for the conversation between the user and the bot.
    state = await conversation_state.get(context)

    if hasattr(state, 'counter'):
        state.counter += 1
    else:
        state.counter = 1

    with open('examples.txt', 'r') as dataset_file:
        data = dataset_file.readlines()
        data = [item.strip().split('\n') for item in data]
    if context.activity.text.upper() == "I WANNA PLAY" or context.activity.text.upper() == "NEXT":
        curr = data[randint(0,len(data))][0]
        #await context.send_activity(f'{curr}')
    elif context.activity.text.upper() == "GIVE ME A JOB":
        await context.send_activity(f'{state.counter}: Would you rather apply here https://careers.microsoft.com/us/en or do nothing instead?')
    else:
        await context.send_activity(f'Would you rather text NEXT or I WANNA PLAY?')
    response = await create_reply_activity(context.activity, f'{state.counter}: {curr}')
    await context.send_activity(response)
    return web.Response(status=202)


async def handle_conversation_update(context: TurnContext) -> web.Response:
    if context.activity.members_added[0].id != context.activity.recipient.id:
        response = await create_reply_activity(context.activity, 'Hi... I am a Would You Rather Game. Text NEXT or I WANNA PLAY to play! Watch out for easter eggs ;)')
        await context.send_activity(response)
    return web.Response(status=200)


async def unhandled_activity() -> web.Response:
    return web.Response(status=404)


async def request_handler(context: TurnContext) -> web.Response:
    if context.activity.type == 'message':
        return await handle_message(context)
    elif context.activity.type == 'conversationUpdate':
        return await handle_conversation_update(context)
    else:
        return await unhandled_activity()


async def messages(req: web.web_request) -> web.Response:
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers['Authorization'] if 'Authorization' in req.headers else ''
    try:
        return await ADAPTER.process_activity(activity, auth_header, request_handler)
    except Exception as e:
        raise e


app = web.Application()
app.router.add_post('/', messages)

try:
    web.run_app(app, host='localhost', port=PORT)
except Exception as e:
    raise e