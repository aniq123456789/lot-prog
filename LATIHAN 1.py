# 5. Auth Session (DIKEMASKINI: 3 Username, 1 Password)
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<div class='data-card' style='text-align:center;'><h3>🔐 Log Masuk</h3>", unsafe_allow_html=True)
        id_user = st.text_input("ID:")
        pw_user = st.text_input("Password:", type="password")
        
        # Senarai username yang dibenarkan
        allowed_users = ["1", "2", "3"]
        common_password = "admin123"
        
        if st.button("Masuk", use_container_width=True):
            # Semakan jika ID ada dalam senarai DAN password betul
            if id_user in allowed_users and pw_user == common_password:
                st.session_state.auth = True
                st.rerun()
            else: 
                st.error("ID/Password Salah!")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()
