import streamlit as st
import streamlit_portfolio_dashboard as dashboard

login_details = {
  "credentials": {
    "usernames": {
      "jsmith": {
        "email": "kaizhang@yahoo.com",
        "name": "John Smith",
        "password": 123
      },
      "rbriggs": {
        "email": "rbriggs@gmail.com",
        "name": "Rebecca Briggs",
        "password": 456
      }
    }
  },
  "cookie": {
    "expiry_days": 1,
    "key": "some_signature_key",
    "name": "cookie_name_streamlit_authenticator"
  },
  "preauthorized": {
    "emails": [
      "abc@gmail.com"
    ]
  }
}




# placeholder = st.empty()
# placeholder.title("login")

# with placeholder.form("login"):
#     username = st.text_input("username")
#     password = st.text_input("password", type="password")
#     submit_button = st.form_submit_button("submit")


#     if submit_button:
#         if username in login_details["credentials"]["usernames"]:
#             print(f"username: {username} found")
#             print(f"password: {login_details['credentials']['usernames'][username]['password']}")
#             if password == str(login_details["credentials"]["usernames"][username]["password"]):
#                 print(password)
#                 st.success("Login successful")
#                 placeholder.empty()
#                 with placeholder.container():
#                     dashboard.threeTabs()
#             else:
#                 st.error("Login failed")

#st.session_state['login'] = False
if 'login' not in st.session_state:
  login_form = st.form(key='login_form')
  username = login_form.text_input(label='username')
  password = login_form.text_input(label='password', type='password')
  submit_button = login_form.form_submit_button(label='submit')


  if submit_button:
    if username in login_details["credentials"]["usernames"]:
        if password == str(login_details["credentials"]["usernames"][username]["password"]):
            st.session_state.username = username
            st.session_state['login'] = True
            st.success("Login successful")
            st.experimental_rerun()
        else:
            st.error("Login failed")

if 'login' in st.session_state:
    st.empty()
    dashboard.threeTabs()