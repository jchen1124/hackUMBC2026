import sqlite3
import os
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions

def search_imessages(query: str, top_k: int = 5 ):
    # ---------- 1. Load messages from iMessage ----------
    db_path = os.path.expanduser("out/output.db")
    conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT ROWID, text, handle_id, date 
    FROM message 
    WHERE text IS NOT NULL AND text != ''
    """)
    rows = cursor.fetchall()
    conn.close()

    texts = [row[1] for row in rows]  # text column
    metadata = [
        {
            "handle_id": row[2],
            "date": row[3],
            "rowid": row[0]
        }
        for row in rows
    ]

    print(f"Loaded {len(texts)} messages from chat.db")

    # ---------- 2. Initialize embedding model ----------
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # ---------- 3. Initialize Chroma DB ----------
    client = chromadb.Client(
        chromadb.config.Settings(
            persist_directory=os.path.expanduser("~/.chroma_imessages"),
            anonymized_telemetry=False
        )
    )

    if "imessage_messages" in [c.name for c in client.list_collections()]:
        collection = client.get_collection("imessage_messages")
    else:
        collection = client.create_collection(
            name="imessage_messages",
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        )

    # ---------- 4. Generate unique IDs ----------
    ids = [f"{meta['handle_id']}_{meta['date']}_{meta['rowid']}" for meta in metadata]

    # ---------- 5. Upsert in batches ----------
    BATCH_SIZE = 5000
    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i:i+BATCH_SIZE]
        batch_meta = metadata[i:i+BATCH_SIZE]
        batch_ids = ids[i:i+BATCH_SIZE]

        collection.upsert(
            documents=batch_texts,
            metadatas=batch_meta,
            ids=batch_ids
        )

    print(f"Upserted {len(texts)} messages into vector DB in batches of {BATCH_SIZE}")

    # ---------- 6. Query messages ----------
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )

    # ---------- 7. Safe Mac timestamp conversion ----------
    def mac_to_datetime(mac_ts):
        mac_epoch = datetime(2001, 1, 1)
        # convert nanoseconds or microseconds to seconds if needed
        if mac_ts > 1e12:          # nanoseconds
            seconds = mac_ts / 1_000_000_000
        elif mac_ts > 1e10:        # microseconds
            seconds = mac_ts / 1_000_000
        else:                      # seconds
            seconds = mac_ts
        return mac_epoch + timedelta(seconds=seconds)

    # ---------- 8. Format results as readable strings ----------
    readable_results = []
    if results['documents'][0]:
        for i in range(len(results['documents'][0])):
            doc = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            dt = mac_to_datetime(meta['date']).strftime("%Y-%m-%d")
            readable_results.append(f"{dt}: {doc}")

    joined_list = "\n\n\n".join(readable_results)
    return joined_list

# ------------------- Example Usage -------------------
if __name__ == "__main__":
    user_query = input("Enter your search query: ")
    top_results = search_imessages(user_query, top_k=10)

    print("Top matching messages:")
    print(top_results)
