"""
generate_year_day_chunks.py

Generate text files with year and day-of-year pairs for each date between START_YEAR and END_YEAR.
Each line is formatted as: YEAR DAY_OF_YEAR (e.g., 2025 1 for Jan 1, 2025)
Output split into chunks of max LINES_PER_FILE lines, no trailing blank lines.
"""

from datetime import datetime, timedelta
import os
import math

START_YEAR = 2000
END_YEAR = 2024
LINES_PER_FILE = 1000  # Max rows for HPC parallel job submission is 1000
OUTPUT_DIR = "../../text_inputs/zonal_inputs/"
OUTPUT_PREFIX = "zonal_stats_input"


def generate_year_day_pairs(start_year, end_year):
    pairs = []
    for year in range(start_year, end_year + 1):
        start_date = datetime(year, 1, 1)
        for day_offset in range(367):
            date = start_date + timedelta(days=day_offset)
            if date.year != year:
                break
            pairs.append((year, date.timetuple().tm_yday))
    return pairs


def write_chunked_files(pairs, lines_per_file, output_dir, prefix):
    os.makedirs(output_dir, exist_ok=True)
    total_files = math.ceil(len(pairs) / lines_per_file)
    print(f"Total pairs: {len(pairs)}")
    print(f"Lines per file: {lines_per_file}")
    print(f"Total files to write: {total_files}")

    for i in range(total_files):
        start_idx = i * lines_per_file
        end_idx = start_idx + lines_per_file
        chunk = pairs[start_idx:end_idx]
        if not chunk:
            continue
        filename = os.path.join(output_dir, f"{prefix}_{i+1:03d}.txt")
        # Write lines without extra newline at the end
        with open(filename, "w") as f:
            for j, (year, day) in enumerate(chunk):
                line = f"{year} {day}"
                # Only add newline if NOT the last line in chunk
                if j < len(chunk) - 1:
                    f.write(line + "\n")
                else:
                    f.write(line)
        print(f"Wrote {len(chunk)} entries to {filename}")


def main():
    pairs = generate_year_day_pairs(START_YEAR, END_YEAR)
    write_chunked_files(pairs, LINES_PER_FILE, OUTPUT_DIR, OUTPUT_PREFIX)
    print("Done.")


if __name__ == "__main__":
    main()
