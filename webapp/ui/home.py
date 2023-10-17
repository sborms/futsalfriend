import streamlit as st


def make_page_home():
    st.header("Welcome to Futsal Friend, your digital futsal companion")

    st.write(
        """
        **Futsal Friend** is a simple web application that provides a few useful
        services to people that love futsal as way to enjoy sports and maximize
        time with friends.
        
        There are four things you can do:
        - Spot a potential **opponent** for a friendly match
        - Find a **team** to join as a player
        - Compare your game **stats** to those of others
        - Get jolly **advice** for your team or yourself as a player
        """
    )

    st.write(
        """
        The data is currently sourced solely from the amazing Belgian amateur futsal
        organisation [lzvcup.be](https://www.lzvcup.be), housing 900+ teams. This app
        should be seen as nothing more than a complement, not as a replacement. All
        data used here is publicly available on the organisation's website.
        """
    )

    st.write(
        """
        _Futsal Friend is still in early stage of development. Check out the
        [GitHub repo](https://github.com/sborms/futsalfriend) if you would
        like to contribute._
        """
    )
