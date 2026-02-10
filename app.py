from flask import Flask, render_template, request
from openai import OpenAI
import os
from dotenv import load_dotenv
import base64
import re

load_dotenv()  # Load environment variables from .env

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def format_analysis_text(text):
    """Convert markdown-like formatting to HTML for better display"""
    # Convert **bold** to <strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert bullet points (- ) to HTML list items
    lines = text.split('\n')
    formatted_lines = []
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        
        # Check if line is a bullet point
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                formatted_lines.append('<ul style="margin-left: 20px; margin-top: 10px;">')
                in_list = True
            # Remove the bullet marker and wrap in <li>
            bullet_text = stripped[2:]
            formatted_lines.append(f'<li style="margin-bottom: 8px;">{bullet_text}</li>')
        else:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            if stripped:  # Only add non-empty lines
                formatted_lines.append(f'<p style="margin-bottom: 12px;">{stripped}</p>')
    
    # Close list if still open
    if in_list:
        formatted_lines.append('</ul>')
    
    return ''.join(formatted_lines)

@app.route("/", methods=["GET", "POST"])
def index():
    result_text = None
    result_text_formatted = None
    result_image = None
    dream_input = ""
    
    if request.method == "POST":
        dream_input = request.form.get("prompt", "")
        
        if dream_input:
            try:
                # Generate Jungian dream analysis text using Responses API
                jungian_analysis_input = f"""
                Provide a deep psychological interpretation of the following dream based on Carl Jung's analytical psychology principles (Jungian analysis):

                Dream: {dream_input}

                In analysis, consider:
                1. Archetypes present (Shadow, Anima/Animus, Self, Persona, etc.)
                2. Important symbols, figures and settings in the dream and their possible meanings
                3. Emotional tone of the dream
                4. Psychological tensions or complexes the dream may reflect

                Provide a thoughtful, insightful interpretation that helps the dreamer understand the unconscious messages.

                Structure response as follows and limit the length to around 200 words:

                [Write a cohesive psychological interpretation of the dream using Jungian concepts in 2-3 senetences.]

                Key Symbols and Archetypes:
                - [List major symbols and archetypes with brief meanings]
                - [Each as a separate bullet point]

                Emotional Tone:
                [Describe the dominant emotions in the dream , in 2-3sentences.]

                **Psychological Theme:**
                [Summarize the unconscious issue or developmental process suggested by the dream, in 2 sentences.]
                """

                # Use the Responses API for text generation
                text_response = client.responses.create(
                    model="gpt-4.1",
                    input=[
                        {"role": "developer", "content": "You are an expert Jungian dream analyst with deep knowledge of Carl Jung's analytical psychology, archetypes, and the collective unconscious."},
                        {"role": "user", "content": jungian_analysis_input}
                    ],
                    temperature=0.9,
                    max_output_tokens=400 #increased the max token
                )
                
                # Access the response using output_text
                result_text = text_response.output_text
                
                # Format the text for HTML display
                result_text_formatted = format_analysis_text(result_text)
                
                # Generate dream image 
                image_prompt = f"""
                    Create a surreal, dreamlike visual representation inspired by Carl Jung's analytical psychology.

                    Use the following Jungian dream interpretation as the conceptual basis
                    for the image. Translate the psychological themes, archetypes, symbols,
                    and emotional atmosphere into visual form.

                    Dream being visualized: {dream_input}

                    Visual guidelines:
                    - Symbolic rather than literal
                    - Surreal and painterly in the style of Inside Out memory orbs
                    - Dreamlike lighting with rich, vibrant colors
                    - Archetypal imagery that represents the unconscious
                    - Introspective and mysterious mood
                    - Glowing, ethereal quality like a memory sphere
                    """

                image_response = client.images.generate(
                    model="gpt-image-1",
                    prompt=image_prompt,
                    n=1,
                    size="1024x1024"
                )
                
                # Get base64 image data
                result_image = image_response.data[0].b64_json
                
            except Exception as e:
                result_text_formatted = f"<p style='color: #d32f2f;'><strong>Error generating analysis:</strong> {str(e)}</p>"
                result_image = None
    
    return render_template("index.html", 
                         result_text=result_text_formatted, 
                         result_image=result_image,
                         dream_input=dream_input)

if __name__ == "__main__":
    app.run(debug=True)