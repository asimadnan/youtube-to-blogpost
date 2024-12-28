import openai
import json
import os
from openai import OpenAI

class BlogPostGenerator:
    def __init__(self, config_path="config.json"):
        self.load_config(config_path)

    def load_config(self, config_path):
        with open(config_path, "r") as config_file:
            self.config = json.load(config_file)

    def read_transcript(self, transcript_path):
        with open(transcript_path, "r") as transcript_file:
            return transcript_file.read()

    def generate_blog_post(self, transcript):
        prompt = self.config["system_prompt"].replace("{{transcript}}", transcript)
        client = OpenAI()

        response = client.chat.completions.create(
            model="o1-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        }
                    ],
                }
            ],
        )

        return response.choices[0].message.content

    def save_blog_post(self, content, output_path):
        with open(output_path, "w") as output_file:
            output_file.write(content)


if __name__ == "__main__":
    CONFIG_PATH = "config.json"
    TRANSCRIPT_PATH = "output/How-Id-learn-ML-in-2024-if-I-could-start-over.txt"
    OUTPUT_PATH = "How-Id-learn-ML-in-2024-if-I-could-start-over.md"

    # Initialize blog post generator
    generator = BlogPostGenerator(CONFIG_PATH)

    # Read transcript
    transcript = generator.read_transcript(TRANSCRIPT_PATH)

    # Generate blog post
    blog_post = generator.generate_blog_post(transcript)

    # Save blog post
    generator.save_blog_post(blog_post, OUTPUT_PATH)

    print(f"Blog post saved to {OUTPUT_PATH}.")
