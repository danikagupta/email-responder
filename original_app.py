import streamlit as st

from graph import *

# Derived from https://colab.research.google.com/drive/1WemHvycYcoNTDr33w7p2HL3FF72Nj88i?usp=sharing

 
st.title("Email responder")
draft_email="""
I am emailing to say that I had a wonderful stay at your resort last week. \n

I really appreciate what your staff did

Thanks,
Paul
"""
if EMAIL := st.text_area("Type in customer email here",height=200,value=draft_email):
    inputs = {"initial_email": EMAIL,"research_info": None, "num_steps":0}
    output = app.invoke(inputs)

    st.write("\n\n******** Final Email ************\n\n")
    st.write(output['final_email'])
    st.write("\n\n******** Details *************\n\n")
    st.write(output)