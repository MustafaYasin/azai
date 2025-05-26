import torch
torch.classes.__path__ = []
import streamlit as st
from rag.generation import Generator
from rag.retrieval import Retriever

from frontend.auth import authenticate
from frontend.settings import settings


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="PureChat",
        page_icon="🌐",
        layout="wide"
    )

    # Hide the sidebar and apply styling
    st.markdown("""
        <style>
        section[data-testid="stSidebar"] {display: none;}

        /* Styling for search results */
        .search-result {
            margin: 10px 0;
            padding: 10px;
            border-radius: 4px;
            background-color: #f0f2f6;
        }
        .search-result summary {
            cursor: pointer;
            color: #0f52ba;
            font-weight: 500;
        }
        .search-result summary:hover {
            color: #1e90ff;
        }
        .metadata {
            font-size: 0.9em;
            color: #666;
            font-style: italic;
        }

        /* Center the content area */
        .center-content {
            max-width: 1000px;
            margin: 0 auto;
            padding: 0 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Check authentication
    if not authenticate():
        return  # Stop if not authenticated

    # If we're authenticated, we can show the chat interface

    # Verwende einen Container nur für den Hauptinhalt, nicht für das Chat-Eingabefeld
    content_container = st.container()

    with content_container:
        # Füge eine Klasse zum Zentrieren des Inhalts hinzu
        st.markdown('<div class="center-content">', unsafe_allow_html=True)

        # Header
        st.title("PureChat 🐉")
        st.subheader("Technischer Experte für Bauvorschriften 👨‍🔧")

        # Initialize session state for messages if it doesn't exist
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "context" not in st.session_state:
            st.session_state.context = None

        # Get API key from settings
        api_key = settings.openai_key

        if not api_key:
            st.error('OpenAI API-Schlüssel nicht gefunden. Bitte überprüfen Sie Ihre .env-Datei.')
            st.stop()

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Document context display logic
        if st.session_state.context and len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
            with st.status("Gefundene relevante Abschnitte", expanded=False) as status:
                st.write("Relevante Abschnitte gefunden:")

                # Display document chunks
                for chunk in st.session_state.context:
                    source = chunk.chunk_title
                    page = f"p. {chunk.page_number + 1}" if chunk.page_number is not None else ""
                    title = chunk.meta.get("title", "Unbenannter Abschnitt")

                    st.markdown(
                        f"""
                        <div class="search-result">
                            <details>
                                <summary>{source} {page}</summary>
                                <div class="metadata">Abschnitt: {title}</div>
                                <div style="margin-top: 8px;">{chunk.chunk_content}</div>
                            </details>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        # Schließe den zentrierten Content-Container
        st.markdown('</div>', unsafe_allow_html=True)

    # Chat input AUSSERHALB des Containers, damit es automatisch unten positioniert wird
    prompt = st.chat_input("Stellen Sie eine Frage zu den Dokumenten...")

    if prompt:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})

        with content_container:
            # Wieder den Zentrier-Container öffnen
            st.markdown('<div class="center-content">', unsafe_allow_html=True)

            with st.chat_message("user"):
                st.markdown(prompt)

            # Schließe den zentrierten Content-Container
            st.markdown('</div>', unsafe_allow_html=True)

        # Retrieve context
        with st.spinner('Suche nach relevanten Informationen...'):
            retriever = Retriever(api_key=api_key)
            relevant_chunks = retriever.find_relevant_chunks(prompt, k=3)

            st.session_state.context = relevant_chunks
            st.rerun()

    # Generate response if needed
    if (len(st.session_state.messages) > 0 and
            st.session_state.messages[-1]["role"] == "user" and
            st.session_state.context is not None):

        with st.spinner('Generiere Antwort...'):
            generator = Generator(api_key=api_key)

            with content_container:
                # Wieder den Zentrier-Container öffnen
                st.markdown('<div class="center-content">', unsafe_allow_html=True)

                with st.chat_message("assistant"):
                    stream = generator.generate_streaming_answer(
                        st.session_state.messages[-1]["content"],
                        k=3,
                        temperature=0
                    )
                    response = st.write_stream(stream)

                # Schließe den zentrierten Content-Container
                st.markdown('</div>', unsafe_allow_html=True)

            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.context = None

if __name__ == "__main__":
    main()
