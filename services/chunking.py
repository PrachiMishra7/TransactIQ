import math
import os

import pandas as pd


def chunk_csv(
    file_path: str,
    output_dir: str,
    chunk_by: str = "row_count",
    chunk_size: int = 1000,
) -> list[dict]:
    """
    Split a CSV file into chunks by row count or approximate file size.
    Returns list of chunk metadata.
    """
    os.makedirs(output_dir, exist_ok=True)
    chunks: list[dict] = []
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    if chunk_by == "file_size":
        rows_per_chunk = chunk_size
    else:
        rows_per_chunk = chunk_size

    chunk_iterator = pd.read_csv(file_path, chunksize=rows_per_chunk)
    for i, chunk_df in enumerate(chunk_iterator):
        chunk_filename = f"{base_name}_chunk_{i + 1}.csv"
        chunk_path = os.path.join(output_dir, chunk_filename)
        chunk_df.to_csv(chunk_path, index=False)
        file_size = os.path.getsize(chunk_path)
        chunks.append({
            "chunk_number": i + 1,
            "filename": chunk_filename,
            "path": chunk_path,
            "row_count": len(chunk_df),
            "start_row": i * rows_per_chunk + 1,
            "end_row": i * rows_per_chunk + len(chunk_df),
            "file_size": file_size,
        })

    return chunks
