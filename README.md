docker build -t streamlit_portfolio_management:beta .
docker run -d -p 8088:8501 --name streamlit_port_mgmt streamlit_portfolio_management:beta

http://<ip-of-wsl2>:8088/