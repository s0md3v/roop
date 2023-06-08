import streamlit as st
from io import StringIO
from streamlit_extras.switch_page_button import switch_page
st.set_page_config(layout="wide", page_title='Roop')
with open('wave.css') as f:
    css = f.read()

st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

VidDone = False
ImgDone = False

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

# Contact Info
st.write("""
         <div align="center">
         <a href="https://github.com/sponsors/s0md3v">Support me ❤️</a>
         </div>
         """, unsafe_allow_html=True)





main, log = st.columns(2)#[4, 1]
with main:
    st.write("---")
    fast_center("Select a Face", 2)
    placeholder = st.empty()
    placeholder.file_uploader('Upload a face image', type=["jpg", "jpeg", "png"], key="face", accept_multiple_files=False)
    #show the image
    face = st.session_state.get("face", None)
    
    
    if face:
        with st.columns(3)[1]: # https://stackoverflow.com/questions/70932538/how-to-center-the-title-and-an-image-in-streamlit
            img = st.image(face, width=300)
        placeholder.empty() 
        
        #try again button
        buttonholder = st.empty()
        buton = buttonholder.button("Try again")
        ImgDone = True
        if buton:
            ImgDone = False
            placeholder.file_uploader("Upload a face image", type=["jpg", "jpeg", "png"], accept_multiple_files=False)
            #delete the image
            img.empty()
            buttonholder.empty()
            


        
            
        
        
        
        
        
with log:
    st.write("---")
    fast_center("Select a Target", 2)
    placeholder2 = st.empty()
    vid = placeholder2.file_uploader("Upload a target video", type=["mp4"], key="target", accept_multiple_files=False)
    
    target = st.session_state.get("target", None)
    
    
    if target:
        fast_center("still working on this button, sorry", 0)
        placeholder2.empty()
        
        VidDone = True
        
        #try again button
        buttonholder2 = st.empty()
        buton2 = buttonholder2.button("Select Again", key='randomshit1')
        if buton2:  
            VidDone = False
            placeholder2.file_uploader("Upload a target video", type=["mp4"], accept_multiple_files=False)
            buttonholder2.empty()


with st.columns(3)[1]:
    with st.columns(3)[1]:
        if VidDone and ImgDone:
            
            # m = st.markdown("""
            #     <style>
            #     div.stButton > button:first-child {
            #     }
            #     </style>""", unsafe_allow_html=True)
            
            if st.button('Next', key='randomshit2'):
                switch_page("Foo")
    


    








