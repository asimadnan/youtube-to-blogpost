import csv
import os
from fetch_transcripts import process_url
from transcript_to_blog import BlogPostGenerator

def ensure_directories():
    """Ensure required directories exist."""
    os.makedirs("data/transcripts", exist_ok=True)
    os.makedirs("data/blogs", exist_ok=True)

def read_unprocessed_urls(input_csv):
    """Read unprocessed URLs from the CSV file."""
    unprocessed_urls = []
    with open(input_csv, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["processed"].lower() != "true":
                unprocessed_urls.append(row["url"])
    return unprocessed_urls

def mark_url_as_processed(input_csv, url):
    """Mark a URL as processed in the CSV file."""
    rows = []
    with open(input_csv, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    with open(input_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["url", "processed"])
        writer.writeheader()
        for row in rows:
            if row["url"] == url:
                row["processed"] = "True"
            writer.writerow(row)

def fetch_transcript(url):
    """Fetch transcript for a YouTube URL."""
    print(f"Fetching transcript for: {url}")
    video_title = process_url(url, "en")  # Assuming 'en' for English language
    transcript_path = os.path.join("data/transcripts", f"{video_title}.txt")
    print(f"transcript_path : {transcript_path}")
    return transcript_path

def generate_blog(transcript_path):
    """Generate blog post from a transcript."""
    print(f"Generating blog for transcript: {transcript_path}")
    config_path = "config.json"
    output_path = transcript_path.replace("transcripts", "blogs").replace(".txt", ".md")

    generator = BlogPostGenerator(config_path)
    transcript = generator.read_transcript(transcript_path)
    blog_post = generator.generate_blog_post(transcript)
    generator.save_blog_post(blog_post, output_path)

    print(f"Blog post saved to: {output_path}")
    return output_path

def main():
    input_csv = "input_url.csv"
    ensure_directories()

    # Read unprocessed URLs
    unprocessed_urls = read_unprocessed_urls(input_csv)

    if not unprocessed_urls:
        print("No unprocessed URLs found. Exiting.")
        return

    # Process each URL
    for url in unprocessed_urls:
        try:
            # Fetch transcript
            transcript_path = fetch_transcript(url)

            # Generate blog
            generate_blog(transcript_path)

            # Mark as processed
            mark_url_as_processed(input_csv, url)

        except Exception as e:
            print(f"Error processing URL {url}: {e}")

if __name__ == "__main__":
    main()
