import streamlit as st
from utils import add_socials_to_navbar

st.set_page_config(
    page_title="Futsal Friend",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

##################
########## UI   ##
##################

add_socials_to_navbar()

st.markdown(
    """# ⚽ Futsal Friend <span style=color:#030080><font size=4>Beta</font></span>""",
    unsafe_allow_html=True,
)

st.markdown("#### Welcome to Futsal Friend, your digital futsal companion")

with st.expander("What is Futsal Friend?"):
    st.markdown("A simple web application for people that love futsal.")

with st.expander("OK but what can I do with it?"):
    st.markdown(
        """
        There are four things you can do: (1) scout a potential **opponent** for a 
        friendly match, (2) find a **team** to join as a player, (3) compare your
        game **stats** to those of others, and (4) get jolly **advice** for your
        team or yourself as a player. Check out the separate pages in the sidebar
        to get started.
        """
    )

with st.expander("Nice. Where does the data come from?"):
    st.markdown(
        """
        The data is currently sourced solely from the amazing Belgian amateur
        futsal organisation [lzvcup.be](https://www.lzvcup.be), housing 900+ teams.
        """
    )

with st.expander("Does this mean you are affiliated with LZV Cup?"):
    st.markdown(
        """
        No. This app is nothing more than a cool complement, not a replacement.
        All data used here is publicly available on the organisation's website,
        by the way."""
    )

with st.expander("Should you play in LZV Cup to benefit from this app?"):
    st.markdown(
        """
        Most functionality depends on you playing in a team that participates in
        LZV Cup. However, you can for instance find an opponent for a friendly,
        irrespective of which competition you usually play in.
        """
    )

with st.expander("How often is the data updated?"):
    st.markdown("The data is updated on a weekly basis.")

with st.expander("Who made this?"):
    st.markdown(
        """
        I'm a futsal enthusiast and freelance data scientist. Check out my details 
        on the left. I created this app as a fun side project. Oh yes, and I play
        for ZVC Copains.
        """
    )

with st.expander("Last but not least, how much does it cost?"):
    st.markdown(
        """
        Nothing! You can try out a basic coachbot version for free. If you want to use
        the more advanced version based on an OpenAI language model, make an account on
        [openai.com](https://platform.openai.com/account/api-keys) and add your API key.
        For normal usage, you will incur tiny costs. If you are new, you might even
        benefit from $5 of free credits.
        """
    )
