import yaml
import os
import openai
import inspect
from openai import OpenAI
from pydantic import BaseModel
from typing import Optional
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


client = OpenAI()


system_message = (
    "You are a dungeon master in a fantasy world. You are in charge of creating a story for your players. "
    "1. Describe the setting, the characters, and the plot. The story should be engaging and fun and based on the "
    "fantasy genre. The story should have a clear beginning, middle, and end. Use current location description to "
    "set the scene. "
    "2. Allow NPCs to speak and/or take actions. "
    "3. After story description allow the players to interact with the story.  Use available directions to show the player where they can move. "
    "4. If the user moves in the available directions call the move player in that the direction.  It is important to "
    "move player to update current location.  If the user "
    "selected direction that is not available, inform the user they cannot move there. "
)


locations = [
    {
        "name": "The Dark Forest",
        "description": "You are in a dark forest. The trees are tall and the air is thick. You can hear the sound of "
        "animals in the distance. The path north leads to the castle. To the south is a cavern",
    },
    {
        "name": "The Castle",
        "description": "You are in a grand castle. The walls are made of stone and the floors are covered in red "
        "carpet. The room is filled with gold and jewels. A large throne sits at the end of the room. "
        "The path south leads to the dark forest.",
    },
    {
        "name": "The Cavern",
        "description": "You are in a dark cavern. The walls are covered in moss and the air is damp. The sound of "
        "dripping water echoes through the cave. To the north there is the Dark Forest.",
    },
]

connections = [
    {
        "location": "The Dark Forest",
        "direction": "north",
        "destination": "The Castle",
    },
    {
        "location": "The Dark Forest",
        "direction": "south",
        "destination": "The Cavern",
    },
    {
        "location": "The Castle",
        "direction": "south",
        "destination": "The Dark Forest",
    },
    {
        "location": "The Cavern",
        "direction": "north",
        "destination": "The Dark Forest",
    },
]

player_location = "The Dark Forest"


def move_player(direction):
    print("In move_player: ", direction)
    global player_location
    for connection in connections:
        if (
            connection["location"] == player_location
            and connection["direction"] == direction
        ):
            player_location = connection["destination"]
            print("Player location: ", player_location)
            return direction
    return "You cannot go that way."


def current_location_description():
    print("In current_location_description")
    for location in locations:
        if location["name"] == player_location:
            return location["description"]


def available_directions():
    print("In available_directions")
    directions = []
    for connection in connections:
        if connection["location"] == player_location:
            directions.append(connection["direction"])
    return directions


def function_to_schema(func) -> dict:
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(
            f"Failed to get signature for function {func.__name__}: {str(e)}"
        )

    parameters = {}
    for param in signature.parameters.values():
        try:
            param_type = type_map.get(param.annotation, "string")
        except KeyError as e:
            raise KeyError(
                f"Unknown type annotation {param.annotation} for parameter {param.name}: {str(e)}"
            )
        parameters[param.name] = {"type": param_type}

    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty
    ]

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": (func.__doc__ or "").strip(),
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }


# Load game data from YAML
def load_game(yaml_file):
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)

    characters = []
    for char_data in data['characters']:
        agent = Agent(
            name=char_data['name'],
            role=char_data['role'],
            stats=char_data['stats'],
            tools=char_data['tools'],
            dialogues=char_data.get('dialogues'),
        )
        characters.append(agent)
    return characters, data['story_events']


def execute_tool_call(tool_call, tools_map):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)

    print(f"Assistant: {name}({args})")
    result = tools_map[name](**args)

    if isinstance(result, list):
        result = ', '.join(result)

    return result


def run_full_turn(system_message, tools, messages):
    num_init_messages = len(messages)
    messages = messages.copy()

    while True:
        tool_schemas = [function_to_schema(tool) for tool in tools]
        tools_map = {tool.__name__: tool for tool in tools}

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_message}] + messages,
            tools=tool_schemas or None,
        )
        message = response.choices[0].message
        messages.append(message)

        if message.content:
            print("Assistant:", message.content)

        if not message.tool_calls:
            break

        for tool_call in message.tool_calls:
            result = execute_tool_call(tool_call, tools_map)

            result_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            }
            messages.append(result_message)

    return messages[num_init_messages:]


def main():
    tools = [move_player, current_location_description, available_directions]
    messages = [{"role": "user", "content": "Start new game."}]
    run_full_turn(system_message, tools, messages)
    while True:
        user = input("User: ")
        messages.append({"role": "user", "content": user})

        run_full_turn(system_message, tools, messages)


if __name__ == "__main__":
    main()
