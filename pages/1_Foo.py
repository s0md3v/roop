import streamlit as st
import  streamlit_toggle as tog


def fast_center(tx, heading=2, raw=False, align='center'):
    #from 0 being none to 6
    if heading > 0:
        text_to_write = f"""
        <div align="{align}">
        <h{heading}>{tx}</h{heading}>
        </div>
        
        """
        
    if heading < 1:
        text_to_write = f"""
        <div align="{align}">
        {tx}
        </div>
        
        """
        
    #st.writre (tx) with center div
    
    if raw:
        return text_to_write
    st.write(text_to_write, unsafe_allow_html=True)

# m = st.markdown("""
# <style>
# div.stCheckbox >stCheckbox:first-child {
#     background-color: #ce1126;
#     color: white;
#     height: 3em;
#     width: 12em;
#     border-radius:10px;
#     border:3px solid #000000;
#     font-size:20px;
#     font-weight: bold;
#     margin: auto;
#     display: block;
# }

# div.stCheckbox >stCheckbox:hover {
# 	background:linear-gradient(to bottom, #ce1126 5%, #ff5a5a 100%);
# 	background-color:#ce1126;
# }

# div.stCheckbox >stCheckbox:active {
# 	position:relative;
# 	top:3px;
# }

# </style>""", unsafe_allow_html=True)

m = st.markdown("""
<style>
div.stButton > button:first-child {
    background-color: #ce1126;
    color: white;
    height: 3em;
    width: 12em;
    border-radius:10px;
    border:3px solid #000000;
    font-size:20px;
    font-weight: bold;
    margin: auto;
    display: block;
}

div.stButton > button:hover {
	background:linear-gradient(to bottom, #ce1126 5%, #ff5a5a 100%);
	background-color:#ce1126;
}

div.stButton > button:active {
	position:relative;
	top:3px;
}

</style>""", unsafe_allow_html=True)

with st.columns(3)[1]:
    fast_center("Options Menu")
    
    with st.columns(3)[1]:
        tCheckbox = st.checkbox("Limit FPS to 30", key='flow1')
        tCheckbox_value = st.session_state['flow1'] 
            
        tCheckbox2 = st.checkbox("Keep frames directory", key='flow2')
        tCheckbox_value2 = st.session_state['flow2'] 
        
        
        
        
        
    
    st.button('Example Confirm/Start Button')
    

    
        
        