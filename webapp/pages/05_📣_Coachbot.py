import time

import openai
import queries
import streamlit as st
import utils
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate

st.set_page_config(page_title="Coachbot", page_icon="📣", layout="wide")


@st.cache_resource
def load_chain(bot_type="Advanced", context=""):
    """Configures a conversational chain for answering user questions."""
    # load basic or advanced language model
    if "Advanced" in bot_type:
        llm = ChatOpenAI(
            temperature=0.7, model="gpt-3.5-turbo", openai_api_key=openai.api_key
        )

    # create chat history memory
    memory = ConversationBufferWindowMemory(k=2, memory_key="history")

    # create system prompt
    prefix = f"""
    You are an AI assistant that provides advice to futsal teams.
    Futsal is played 5-a-side on a small indoor field.
    You are given the following information and a question.
    Provide a conversational answer. Be witty but concise. Don't make up an answer.
    If the question is not about futsal, inform that you are tuned
    to only answer questions about futsal.

    This is relevant information about the team and competition:
    {context}
    """
    template = (
        prefix
        + """
    History: {history}
    Question: {input}
        
    Helpful answer here, in Dutch:
    """
    )

    # define prompt template
    prompt = PromptTemplate(input_variables=["history", "input"], template=template)

    # Create the conversational chain
    chain = ConversationChain(prompt=prompt, llm=llm, memory=memory, verbose=True)

    return chain


def prepare_prompt_team_context(dict_info):
    """Prepares a string with team and player stats for the prompt."""
    context = ""
    for title, df in dict_info.items():
        context += title + ":\n" + df.to_string(index=False) + "\n\n"
    return context


conn = utils.connect_to_sqlite_db()

# openai.api_key = st.secrets["OPENAI_API_KEY"]

##################
########## UI   ##
##################

avatar = "assets/capi.png"

with st.sidebar:
    with st.container():
        bot_type = st.radio(
            "Choose a type of bot",
            ["Basic", ":red[Advanced]"],
            captions=[
                "Free but not as accurate.",
                "Not entirely free but more capable.",
            ],
            index=1,
        )
        if "Advanced" in bot_type:
            st.info(
                """
                Enter your OpenAI API key to use the advanced **GPT-3.5 Turbo**
                language model. We won't expose your key! Information about pricing
                is [here](https://openai.com/pricing#language-models).
                """
            )
            input_openai_key = st.text_input(
                "Paste your OpenAI API key here",
                type="password",
                placeholder="sk-...",
            )

            # add and destroy API key
            openai.api_key = input_openai_key
            del input_openai_key

st.title("💬 Coachbot")
st.markdown("### Seek advice from an AI futsal coach")

df_teams = queries.query_list_teams(conn)

if "team" not in st.session_state:
    st.session_state["team"] = None

# ask for team first
if st.session_state["team"] is None:
    col1, _, _ = st.columns(3)
    team = col1.selectbox(
        "First tell me what team you play for",
        options=df_teams["team"].tolist(),
        index=None,
    )
    st.session_state["team"] = team

    st.button("Let's chat!")

# initialize chat window
else:
    st.markdown("*Take what the bot says with a grain of salt.*")

    # get relevant information to add as context to prompt
    team = st.session_state["team"]

    df_schedule = queries.query_schedule(conn, team)

    df_stats_players = queries.query_stats_players(conn, team=team)

    oponnent_1 = [who for who in df_schedule.loc[0][1:].tolist() if who != team][0]
    df_stats_players_oponnent_1 = queries.query_stats_players(conn, team=oponnent_1)

    df_standings = queries.query_standings(conn, team=team)

    dict_info = {
        "Competition standings": df_standings,
        "Schedule": df_schedule,
        "Player statistics": df_stats_players,
        "Player statistics next opponent": df_stats_players_oponnent_1,
    }
    context = prepare_prompt_team_context(dict_info)

    # configure chain
    chain = load_chain(bot_type=bot_type, context=context)

    # initialize chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": f"Cool, {team} is a great team! How can I help?",
            }
        ]

    # display chat messages from history on app rerun
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])
        else:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if query := st.chat_input("Talk to me..."):
        # display user message
        with st.chat_message("user"):
            st.markdown(query)

        # add user message to chat history
        st.session_state.messages.append({"role": "user", "content": query})

        # display chatbot message
        with st.chat_message("assistant", avatar=avatar):
            # send user's question to chain
            result = chain({"input": query})
            response = result["response"]

            message_placeholder, full_response = st.empty(), ""
            for chunk in response.split():
                full_response += chunk + " "
                time.sleep(0.05)  # simulate stream of response with milliseconds delay
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        # add assistant message to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
