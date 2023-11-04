import streamlit as st
import pickle
from code_editor import code_editor


tables_query = """-- To show all available tables, run the following query.
-- Shortcut: Cmd+Enter or Ctrl+Enter to run query
SELECT table_name AS available_tables
FROM INFORMATION_SCHEMA.tables
WHERE table_schema = 'public';"""

disallowed = ['update', 'insert', 'alter', 'delete', 'rename', 'create', 'into', 'add', 'drop', 'truncate']

def clear_text():
    st.session_state.user_answer = st.session_state.answerbox
    st.session_state.answerbox = ""

def reset_query():
    st.session_state.sqlbox = {'text': tables_query}
    st.session_state.user_answer = ""

if 'user_answer' not in st.session_state:
    st.session_state.user_answer = ""

if 'level' not in st.session_state:
    st.session_state.level = 1

if 'user_query' not in st.session_state:
    st.session_state.user_query = tables_query

with open('levels_data.pkl', 'rb') as handle:
    levels_data = pickle.load(handle)

# Running story text
st.sidebar.title("SQL Detective")

level = st.session_state.level
st.sidebar.subheader(f"Part {levels_data[level]['part'][0]}: {levels_data[level]['part'][1]}")
st.sidebar.markdown(f"`Level {str(level)}`")
st.sidebar.markdown(levels_data[st.session_state.level]["story"])

sql_tab, help_tab = st.tabs(["Enter your SQL query", "Help"])

# Developing code editor interface
with sql_tab:
    custom_btns = [{
    "name": "Run",
    "feather": "Play",
    "primary": True,
    "hasText": True,
    "showWithIcon": True,
    "commands": ["submit"],
    "alwaysOn": True,
    "style": {"bottom": "0.44rem", "right": "0.4rem"}
    }
    ]

    css_string = '''
    background-color: #bee1e5;

    body > #root .ace-streamlit-dark~& {
    background-color: #262830;
    }

    .ace-streamlit-dark~& span {
    color: #fff;
    opacity: 0.6;
    }

    span {
    color: #000;
    opacity: 0.5;
    }

    .code_editor-info.message {
    width: inherit;
    margin-right: 75px;
    order: 2;
    text-align: center;
    opacity: 0;
    transition: opacity 0.7s ease-out;
    }

    .code_editor-info.message.show {
    opacity: 0.6;
    }

    .ace-streamlit-dark~& .code_editor-info.message.show {
    opacity: 0.5;
    }
    '''

    # create info bar dictionary
    info_bar = {
    "name": "language info",
    "css": css_string,
    "style": {
                "order": "1",
                "display": "flex",
                "flexDirection": "row",
                "alignItems": "center",
                "width": "100%",
                "height": "2.5rem",
                "padding": "0rem 0.75rem",
                "borderRadius": "8px 8px 0px 0px",
                "zIndex": "9993"
            },
    "info": [{
                "name": "pgsql",
                "style": {"width": "100px"}
            }]
    }

    response_dict = code_editor(st.session_state.user_query,
                                lang="pgsql",
                                height=[5, 20],
                                buttons=custom_btns,
                                key="sqlbox",
                                info=info_bar,
                                props={'placeholder': tables_query,}
                                )

    # Initialize connection.
    conn = st.experimental_connection(levels_data[st.session_state.level]["connection"], type="sql")

    query = response_dict['text'] if response_dict['text'] != "" else tables_query

    if any([phrase in query.lower() for phrase in disallowed]):
        st.error("Error: It appears you may be trying to use a command that is not allowed in this context.  Please reformulate your query to avoid commands that could change data or database configuration.")
    else:
        try:
            df = conn.query(query, ttl=0)
            if not df.empty:
                # Display the result as a DataFrame
                st.dataframe(df,
                            hide_index=True,
                            height=160,
                            width=700,
                            column_config={'row_id': st.column_config.NumberColumn(format="%d"),
                                            'report_id': st.column_config.NumberColumn(format="%d"),
                                            'officer_id_senior': st.column_config.NumberColumn(format="%d"),
                                            'officer_id_junior': st.column_config.NumberColumn(format="%d"),
                                            'motive': st.column_config.TextColumn(),
                                            'opportunity': st.column_config.TextColumn(),
                                            'means': st.column_config.TextColumn(),
                                            'case_id': st.column_config.NumberColumn(format="%d"),
                                            }
                            )
                st.write(f"Returned {len(df)} records.")
            else:
                st.write("No results to display.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    # Answer Submission Box
    st.subheader("Solve the Puzzle")
    st.text_input("Input your answer and press 'Enter'", key="answerbox", on_change=clear_text)
    user_answer = st.session_state.user_answer
    answer_result = st.empty()

    # Submit answer logic
    correct_answers = levels_data[st.session_state.level]["answers"]
    if user_answer == "":
        pass
    elif user_answer.lower().replace(" ", "").replace("-", "").replace("1st", "first") in correct_answers:
        st.session_state.level += 1
        answer_result.success(f"Correct! Welcome to level {st.session_state.level}")

        proceed = st.button("Proceed to next level", on_click=reset_query)
        if proceed:
            st.rerun()
    else:
        answer_result.error("Incorrect. Try again.")

with help_tab:
    with st.expander("What flavor of SQL does this game use?"):
        st.markdown("""This game uses [PostgreSQL](https://www.postgresql.org/).  For a nice tutorial, see [here](https://www.postgresqltutorial.com/).""")

    with st.expander("What is the query to show available tables again?"):
        st.markdown("""
```
SELECT table_name AS available_tables
FROM INFORMATION_SCHEMA.tables
WHERE table_schema = 'public';
```
        """)
    
    with st.expander("Why am I receiving an error that says the command is not allowed?"):
        st.markdown(f"""Certain strings are not allowed in the text of your SQL query to prevent attempts to alter the database.  Please edit your query to avoid using any of the following substrings which are not allowed:
                    
    {disallowed}
                    
                    """)
 