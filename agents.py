from textwrap import dedent
from agno.agent import Agent
from agno.models.google import Gemini
from agno.models.azure import AzureAIFoundry
from agno.embedder.azure_openai import AzureOpenAIEmbedder
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.storage.agent.sqlite import SqliteAgentStorage
from agno.knowledge.csv import CSVKnowledgeBase
from agno.vectordb.pgvector import PgVector
from pathlib import Path
from google.genai import types
from prompts import *
import os


# Define the current working directory and output directory for saving files
cwd = Path(__file__).parent
output_dir = cwd.joinpath("output")
# Create output directory if it doesn't exist
output_dir.mkdir(parents=True, exist_ok=True)
# Create tmp directory if it doesn't exist
tmp_dir = cwd.joinpath("tmp")
tmp_dir.mkdir(parents=True, exist_ok=True)

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge_base = CSVKnowledgeBase(
    path="data/pokemon_data.csv",
    vector_db=PgVector(
        table_name="pokemon_csv",
        db_url=db_url,
        embedder=AzureOpenAIEmbedder(),
    ),
    num_documents=3
)

# Load the knowledge base, comment out after first run
# knowledge_base.load(recreate=False)

def get_narrator():
    agent_storage = SqliteAgentStorage(
    table_name="pokemon_adventure_story",
    db_file=str(tmp_dir.joinpath("agents.db")), 
    )
    narrator = Agent(
        model=Gemini(
            id="gemini-2.0-flash",
            temperature=1.2,
            max_output_tokens=265,
            # There will be attacking and battling other Pokemons so
            # not blocking these will be better for gameplay
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_NONE",
                ),
            ]
        ),
        description=narrator_description,
        instructions=narrator_instructions,
        tools=[DuckDuckGoTools(modifier="site:pokemondb.net")],
        markdown=True,
        add_history_to_messages=True,
        num_history_responses=5,
        read_chat_history=True,
        storage=agent_storage,
        knowledge=knowledge_base,
        search_knowledge=True,
        retries=3,
    )

    return narrator

def get_observer():
    observer_storage = SqliteAgentStorage(
    table_name="pokemon_observer_data",
    db_file=str(tmp_dir.joinpath("observer_agents.db")),
    )
    observer = Agent(
        model=Gemini(
            id="gemini-2.0-flash",
            temperature=0.8,
            api_key=os.environ['GOOGLE_API_KEY_2']
        ),
        description=observer_description,
        instructions=observer_instructions,
        add_history_to_messages=True,
        num_history_responses=5,
        read_chat_history=True,
        storage=observer_storage,
        knowledge=knowledge_base,
        retries=3,
        expected_output=obseserver_expected_output
    )
    return observer