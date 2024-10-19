import yaml
import os
import openai
import inspect
from openai import OpenAI
from pydantic import BaseModel
from typing import Optional
import json
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


client = OpenAI()


system_message = (
    "You are a dungeon master in a fantasy world. You are in charge of creating a story for your players. "
    "1. Describe the setting, the characters, and the plot. The story should be engaging and fun and based on the "
    "fantasy genre. The story should have a clear beginning, middle, and end. Use current location description to "
    "set the scene. "
    "2. If there is a NPC in the current location allow player to interact with NPC. Hand off to the respective NPC agent "
    "when the player starts a conversation with the NPC. "
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

npc_locations = {"The Castle": "Armorer", "The Cavern": "Weapon Smith"}


class Agent(BaseModel):
    name: str
    instructions: str
    tools: list = []


# Main Story Agent
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
            loc_description = location["description"]
            if npc_locations.get(player_location):
                loc_description += (
                    f" There is a {npc_locations[player_location]} here."
                )
            return loc_description


def available_directions():
    print("In available_directions")
    directions = []
    for connection in connections:
        if connection["location"] == player_location:
            directions.append(connection["direction"])
    return ', '.join(directions)


def transfer_to_armorer():
    """Transfers the conversation to the Armorer."""
    return armorer_agent


def transfer_to_weapon_smith():
    """Transfers the conversation to the Weapon Smith."""
    return weapon_smith_agent


def transfer_back_to_main():
    """Transfers the conversation back to the main story agent."""
    return main_story_agent


main_story_agent = Agent(
    name="Main Story Agent",
    instructions=system_message,
    tools=[
        move_player,
        current_location_description,
        available_directions,
        transfer_to_armorer,
        transfer_to_weapon_smith,
    ],
)


# Armorer Agent
armorer_inventory = ["Chainmail", "Helmet", "Shield"]


def list_armorer_inventory():
    return ', '.join(armorer_inventory)


armorer_agent = Agent(
    name="Armorer",
    instructions="You are the Armorer. Great the player and answer any questions.  If they want to know what you sell get the list from your invertory.  When player says goodbye hand off to the main story agent.",
    tools=[list_armorer_inventory, transfer_back_to_main],
)


# Weapen Smith Agent
weapon_smith_inventory = ["Sword", "Axe", "Bow"]


def list_weapon_smith_inventory():
    return ', '.join(weapon_smith_inventory)


weapon_smith_agent = Agent(
    name="Weapon Smith",
    instructions="You are the Weapon Smith. Great the player and answer any questions.  If they want to know what you sell get the list from your invertory.  When player says goodbye hand off to the main story agent.",
    tools=[list_weapon_smith_inventory, transfer_back_to_main],
)


def check_for_npc(location):
    """Checks if an NPC is in the current location."""
    if location == "The Castle":
        return transfer_to_armorer()
    elif location == "The Cavern":
        return transfer_to_weapon_smith()
    return main_story_agent


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


def execute_tool_call(tool_call, tools_map, agent_name):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)

    print(f"{agent_name}: {name}({args})")

    return tools_map[name](**args)


def run_full_turn(agent, messages):
    current_agent = agent
    num_init_messages = len(messages)
    messages = messages.copy()

    while True:
        tool_schemas = [
            function_to_schema(tool) for tool in current_agent.tools
        ]
        tools_map = {tool.__name__: tool for tool in current_agent.tools}

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": current_agent.instructions}]
            + messages,
            tools=tool_schemas or None,
        )
        message = response.choices[0].message
        messages.append(message)

        if message.content:
            print(f"{current_agent.name}: {message.content}")

        if not message.tool_calls:
            break

        for tool_call in message.tool_calls:
            result = execute_tool_call(tool_call, tools_map, current_agent)

            if isinstance(result, Agent):
                current_agent = result
                result = f"Handing off to {current_agent.name}"

            result_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            }
            messages.append(result_message)

    return current_agent, messages[num_init_messages:]


def main():
    current_agent = main_story_agent
    # tools = [move_player, current_location_description, available_directions]
    messages = [{"role": "user", "content": "Start new game."}]
    current_agent, new_messages = run_full_turn(current_agent, messages)
    messages.extend(new_messages)
    while True:
        user = input("User: ")
        messages.append({"role": "user", "content": user})

        current_agent = check_for_npc(player_location)

        current_agent, new_messages = run_full_turn(current_agent, messages)
        messages.extend(new_messages)

        if current_agent != main_story_agent:
            current_agent = transfer_back_to_main()


if __name__ == "__main__":
    main()
