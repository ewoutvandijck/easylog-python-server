# main.py

import asyncio

import mysql.connector

from src.agents.easylog_agent import AnthropicEasylogAgent, AnthropicEasylogAgentConfig

# Maak een connectie met de database
db_connection = mysql.connector.connect(host="localhost", user="root", password="secret", database="easylog_db")

# Maak een cursor die we kunnen doorgeven aan onze agent
cursor = db_connection.cursor()

# Stel de configuratie voor je agent in, als dat nodig is
config = AnthropicEasylogAgentConfig(max_report_entries=100, debug_mode=True, image_max_width=600, image_quality=60)

# Instantieer de agent
agent = AnthropicEasylogAgent(
    config=config,
    easylog_db=db_connection,  # of we geven db_connection door
)


async def run_conversation():
    # Hier roep je de agent aan met wat testberichten:
    user_messages = [{"role": "user", "content": "Hoi, ik wil wat data over de laatste controles."}]
    async for chunk in agent.on_message(user_messages):
        print(chunk)


if __name__ == "__main__":
    asyncio.run(run_conversation())
