
from openai import OpenAI

from rag.retrieval import Retriever


class Generator:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.retriever = Retriever(api_key=api_key)

    def generate_answer(
            self,
            query: str,
            k: int = 3,
            temperature: float = 0,
            custom_prompt: str | None = None
    ) -> str:
        try:
            relevant_chunks = self.retriever.find_relevant_chunks(query, k)

            if not relevant_chunks:
                return "Es wurden keine relevanten Informationen in den Dokumenten gefunden."

            context = self.retriever.format_context(relevant_chunks)

            system_content = custom_prompt or """Sie sind ein technischer Experte, der sich auf Bauvorschriften und technische Richtlinien spezialisiert hat.

Ihre Aufgaben:
- Analysieren Sie die bereitgestellten Dokumentenauszüge gründlich
- Beantworten Sie die Frage basierend auf den tatsächlichen Inhalten der Auszüge
- Zitieren Sie die relevanten Quellen mit Seitenzahlen
- Fassen Sie komplexe technische Informationen klar und verständlich zusammen
- Wenn die Auszüge die relevanten Informationen enthalten, geben Sie diese ausführlich wieder
- Antworten Sie immer auf Deutsch und im Kontext technischer Dokumentation

Wichtig: Basieren Sie Ihre Antwort ausschließlich auf den bereitgestellten Dokumentenauszügen."""

            messages = [
                {
                    "role": "system",
                    "content": system_content
                },
                {
                    "role": "user",
                    "content": f"""Bitte beantworten Sie folgende Frage basierend auf den Dokumentenauszügen:

Frage: {query}

Verfügbare Dokumentenauszüge:
{context}

Anforderungen an die Antwort:
1. Nutzen Sie die Informationen aus den Dokumentenauszügen
2. Zitieren Sie die relevanten Stellen mit Quellenangabe und Seitenzahl
3. Formulieren Sie die Antwort klar und verständlich
4. Falls die Information tatsächlich nicht in den Auszügen zu finden ist, erklären Sie, welche verwandten Informationen verfügbar sind"""
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )

            return response.choices[0].message.content

        except Exception as e:
            error_msg = f"Fehler bei der Antwortgenerierung: {e!s}"
            return error_msg

    def generate_streaming_answer(
            self,
            query: str,
            k: int = 3,
            temperature: float = 0,
            custom_prompt: str | None = None
    ):
        try:
            relevant_chunks = self.retriever.find_relevant_chunks(query, k)

            if not relevant_chunks:
                return "Es wurden keine relevanten Informationen in den Dokumenten gefunden."

            context = self.retriever.format_context(relevant_chunks)

            system_content = custom_prompt or """Sie sind ein technischer Experte, der sich auf Bauvorschriften und technische Richtlinien spezialisiert hat.

Ihre Aufgaben:
- Analysieren Sie die bereitgestellten Dokumentenauszüge gründlich
- Beantworten Sie die Frage basierend auf den tatsächlichen Inhalten der Auszüge
- Zitieren Sie die relevanten Quellen mit Seitenzahlen
- Fassen Sie komplexe technische Informationen klar und verständlich zusammen
- Wenn die Auszüge die relevanten Informationen enthalten, geben Sie diese ausführlich wieder
- Antworten Sie immer auf Deutsch und im Kontext technischer Dokumentation

Wichtig: Basieren Sie Ihre Antwort ausschließlich auf den bereitgestellten Dokumentenauszügen."""

            messages = [
                {
                    "role": "system",
                    "content": system_content
                },
                {
                    "role": "user",
                    "content": f"""Bitte beantworten Sie folgende Frage basierend auf den Dokumentenauszügen:

Frage: {query}

Verfügbare Dokumentenauszüge:
{context}

Anforderungen an die Antwort:
1. Nutzen Sie die Informationen aus den Dokumentenauszügen
2. Zitieren Sie die relevanten Stellen mit Quellenangabe und Seitenzahl
3. Formulieren Sie die Antwort klar und verständlich
4. Falls die Information tatsächlich nicht in den Auszügen zu finden ist, erklären Sie, welche verwandten Informationen verfügbar sind"""
                }
            ]

            return self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True
            )

        except Exception as e:
            error_msg = f"Fehler bei der Antwortgenerierung: {e!s}"
            return error_msg
