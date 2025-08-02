#writefile ingest.py
import pandas as pd
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer

# --- Configuration ---
# Your Supabase credentials
SUPABASE_URL = "https://kxqxtzouxemvcioqhjgm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt4cXh0em91eGVtdmNpb3FoamdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQwNzM1NTAsImV4cCI6MjA2OTY0OTU1MH0.V0MLZaGHl_jDDAbgkM6KHXusXOhGrOwM6D02H7sPjaM"

# The path to your cleaned CSV file in Google Drive.
CSV_FILE_PATH = "/content/opportunity/cleaned_opportunities.csv"

# The name of your Supabase table
SUPABASE_TABLE_NAME = "opportunities"

# The Sentence-Transformers model to use
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# --- Supabase Client Setup ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Sentence-Transformers Model Setup ---
print(f"Loading Sentence-Transformers model: {EMBEDDING_MODEL}...")
model = SentenceTransformer(EMBEDDING_MODEL)
print("Model loaded successfully.")

def generate_embedding(text: str):
    """Generates a sentence embedding for a given text."""
    try:
        embedding = model.encode(text, convert_to_numpy=False).tolist()
        return embedding
    except Exception as e:
        print(f"Error generating embedding for text: '{text[:50]}...' Error: {e}")
        return None

def main():
    """
    Reads a CSV from Google Drive, generates embeddings, and inserts data into Supabase.
    """
    try:
        df = pd.read_csv(CSV_FILE_PATH)
    except FileNotFoundError:
        print(f"Error: The CSV file at '{CSV_FILE_PATH}' was not found.")
        return

    print(f"Processing {len(df)} rows from the CSV file...")

    for index, row in df.iterrows():
        text_to_embed = f"{row['opportunity_title']}. {row['description']}. Link: {row['link']}"
        
        if not text_to_embed.strip():
            print(f"Skipping row {index}: No content to embed.")
            continue

        embedding = generate_embedding(text_to_embed)

        if embedding:
            data_to_insert = row.to_dict()
            data_to_insert['embedding'] = embedding

            try:
                supabase.table(SUPABASE_TABLE_NAME).insert(data_to_insert).execute()
                print(f"Inserted row {index} successfully.")
            except Exception as e:
                print(f"Error inserting row {index} into Supabase: {e}")
        else:
            print(f"Skipping row {index}: Could not generate embedding.")

    print("Data ingestion complete.")

if __name__ == "__main__":
    main()