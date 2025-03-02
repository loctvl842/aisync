from aisync.engines.graph import hook


@hook
def before_read_message(input: str):
    return {"messages": [("human", input)]}


@hook
def before_send_message(message):
    if message[1]["langgraph_node"] == "king":
        return message[0].content
    # return message['messages'][-1][1].content
    # return message
