import streamlit as st

def show_metrics(distance_before,distance_after):

    col1,col2,col3 = st.columns(3)

    with col1:
        st.metric("Distance Before",f"{distance_before:.2f} km")

    with col2:
        st.metric("Distance After",f"{distance_after:.2f} km")

    with col3:
        saving = ((distance_before-distance_after)/distance_before)*100
        st.metric("Optimization Gain",f"{saving:.1f}%")