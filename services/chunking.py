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
    df = pd.read_csv(file_path)
    total_rows = len(df)
    chunks: list[dict] = []

    if chunk_by == "file_size":
        sample_size = min(100, total_rows)
        if sample_size > 0:
            sample = df.head(sample_size).to_csv(index=False)
            bytes_per_row = len(sample.encode("utf-8")) / sample_size
            rows_per_chunk = max(1, int(chunk_size / bytes_per_row))
        else:
            rows_per_chunk = chunk_size
    else:
        rows_per_chunk = chunk_size

    num_chunks = math.ceil(total_rows / rows_per_chunk) if total_rows > 0 else 0
    base_name = os.path.splitext(os.path.basename(file_path))[0]

    for i in range(num_chunks):
        start = i * rows_per_chunk
        end = min((i + 1) * rows_per_chunk, total_rows)
        chunk_df = df.iloc[start:end]
        chunk_filename = f"{base_name}_chunk_{i + 1}.csv"
        chunk_path = os.path.join(output_dir, chunk_filename)
        chunk_df.to_csv(chunk_path, index=False)
        file_size = os.path.getsize(chunk_path)
        chunks.append({
            "chunk_number": i + 1,
            "filename": chunk_filename,
            "path": chunk_path,
            "row_count": len(chunk_df),
            "start_row": start + 1,
            "end_row": end,
            "file_size": file_size,
        })

    return chunks
