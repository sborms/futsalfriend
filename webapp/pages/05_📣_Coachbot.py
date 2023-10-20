import os
import time

import openai
import queries
import streamlit as st
import utils
from dotenv import load_dotenv
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate

st.set_page_config(page_title="Coachbot", page_icon="📣", layout="wide")


@st.cache_resource
def load_chain(context=""):
    """Configures a conversational chain for answering user questions."""
    # load OpenAI chat model
    llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")

    # create chat history memory
    memory = ConversationBufferWindowMemory(k=2, memory_key="history")

    # create system prompt
    prefix = f"""
        You are an AI assistant for providing advice to futsal teams and players.
        You are given the following futsal stats and a question.
        Provide a conversational answer. Be witty and to the point.
        If you don't know the answer, just say
        'Sorry, I don't know... but remember: Offense is the best defense!'.
        Don't try to make up an answer.
        If the question is not about futsal, politely inform that you are tuned
        to only answer questions about futsal.
        
        These are the relevant team and player stats: {context}
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


conn = utils.get_sqlite_connection()

load_dotenv()
# openai.api_key = os.getenv("OPENAI_API_KEY")
# openai.api_key = st.secrets["OPENAI_API_KEY"]

##################
########## UI   ##
##################

st.title("💬 Coachbot")
st.markdown("### Seek advice from an AI futsal coach")

st.markdown("Take what the bot says with a grain of salt.")

avatar = "assets/capi.png"

df_next_games = queries.query_next_games(conn)
chain = load_chain()

# initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "assistant",
            "content": "Hi futsal lover! What team do you play for?",
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

fl_team_found = False
if query := st.chat_input("Talk to me..."):
    # display user message
    with st.chat_message("user"):
        st.markdown(query)

    while not fl_team_found:
        st.session_state.messages.append({"role": "user", "content": query})
        if query in df_next_games["team"]:
            st.session_state["messages"].append(
                {
                    "role": "assistant",
                    "content": "Great team! Coachbot at your service. How can I help?",
                }
            )
            fl_team_found = True
        else:
            oops = "Sorry, I don't know that team. Try again."
            with st.chat_message("assistant"):
                st.markdown(oops)
            st.session_state["messages"].append({"role": "assistant", "content": oops})

    # add user message to chat history
    st.session_state.messages.append({"role": "user", "content": query})

    # display chatbot message
    with st.chat_message("assistant", avatar=avatar):
        # send user's question to chain
        result = chain({"input": query})
        response = result["answer"]

        message_placeholder, full_response = st.empty(), ""
        for chunk in response.split():
            full_response += chunk + " "
            time.sleep(0.05)  # simulate stream of response with milliseconds delay
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)

    # add assistant message to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
