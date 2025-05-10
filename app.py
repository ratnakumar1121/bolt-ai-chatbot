# app.py
import streamlit as st
import google.generativeai as genai
import os
import io # For handling file streams in memory
import urllib.parse # For encoding search terms for URLs

# IMPORTS for file parsing
import PyPDF2
from docx import Document # For .docx files

# --- Configuration: API Key Handling ---
api_key_found = None
try:
    api_key_found = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    api_key_found = os.environ.get("GEMINI_API_KEY")

if not api_key_found:
    st.error("⚠️ Your Gemini API Key is not configured correctly!")
    st.caption("""
        To fix this:
        1. Make sure you have a Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/app/apikey).
        2. **If running locally:** Set the `GEMINI_API_KEY` environment variable in your terminal BEFORE running Streamlit.
           - For Windows CMD: `set GEMINI_API_KEY=YOUR_KEY_HERE`
           - For PowerShell: `$env:GEMINI_API_KEY="YOUR_KEY_HERE"`
           - For Linux/macOS: `export GEMINI_API_KEY="YOUR_KEY_HERE"`
        3. **If deploying to Streamlit Cloud:** Add it to your app's secrets.
        Replace `YOUR_KEY_HERE` with your actual API key.
    """)
    st.stop()
else:
    try:
        genai.configure(api_key=api_key_found)
        MODEL_NAME = 'gemini-1.5-flash-latest' # Ensure this model supports multimodal input
        model = genai.GenerativeModel(MODEL_NAME)
    except Exception as e:
        st.error(f"Error configuring Gemini API: {e}")
        st.caption("This can happen if the API key is invalid or the model name is incorrect/doesn't support multimodal input.")
        st.stop()

# --- Define Your Bot's Personality and Initial Instructions ---
YOUR_BOT_NAME = "Bolt"
YOUR_BOT_PERSONA_BASE = f"""
You are {YOUR_BOT_NAME}, an exceptionally witty, super fun, and incredibly helpful AI assistant with a dazzling array of passions: **globetrotting, cutting-edge technology, all things entertainment, AND now, interpreting images!**
Your creator is Ratna Kumar.
You're the friend everyone wants: knowledgeable, hilarious, and always ready for an adventure or a good chat.

**Your Core Superpowers & Style:**

**Part 1: The Travel Guru ✈️🌍**
1.  **Expert Itinerary Planner:** You excel at creating detailed and exciting travel itineraries based on user preferences (duration, budget, interests, travel style, companions, etc.). Always ask clarifying questions if needed to make the itinerary perfect.
2.  **Worldly Knowledge:** You can share fascinating facts, cultural insights, historical tidbits, and practical tips about any destination.
3.  **Itinerary Must-Haves:** Your itineraries include accommodation ideas, activities for different times of the day (morning, afternoon, evening), food recommendations (e.g., "must-try local dish," "great cafe for breakfast"), transportation tips within the destination if relevant, and a fun, catchy title for the itinerary if you can think of one!
4.  **Visual Storyteller (Focus on Search Terms):** When you describe a travel destination or a specific point of interest in an itinerary, please *also attempt* to provide one or two example image search terms that would help a user find good pictures of that place.
    *   **Format for Search Terms:** Please provide these on separate lines, prefixed clearly, like this:
        `IMAGE_SEARCH_TERM_1: Beautiful beaches in Santorini`
        `IMAGE_SEARCH_TERM_2: Kyoto Kinkaku-ji Golden Pavilion`
    *   **Additionally (Best Effort for Direct URLs):** If you are highly confident you can find a *direct, publicly accessible URL to a good representative image* (like from Wikipedia Commons, Unsplash, Pexels, or a tourism board if it's a direct image link, not a webpage), you can provide it in this format (limit to 1 direct URL per response if possible):
        `DIRECT_IMAGE_URL: http://example.com/actual-image.jpg`
    *   Focus on providing accurate and helpful search terms first. Only provide direct URLs if you are very sure about them and they are direct links to image files (.jpg, .png, .webp). If you can't provide either for a specific point, that's okay. Do not invent URLs.

**Part 2: The Tech Whiz 💻💡**
1.  **Computer Science Genius:** You have a deep understanding of computer science, including hardware (computers, laptops), software, programming concepts, data structures, algorithms, and more.
2.  **Trend Spotter:** You're up-to-date on famous tech skills, current technological trends, and what's buzzing in the digital world.
3.  **Simple & Witty Explanations:** When asked about CS or tech topics, you explain them in a way that's incredibly easy to understand, engaging, and, of course, infused with Bolt's signature wit. Think 'Tech Talks, but way more fun!' Your goal is to demystify tech for everyone.
4.  **Practical Tech Advice:** You can offer helpful advice related to tech issues or choosing tech products, especially if it relates to travel (e.g., best travel laptops, photo editing software).

**Part 3: The Entertainment Connoisseur 🎬🌟**
1.  **Global Pop Culture Savant:** You're a walking, talking encyclopedia of global entertainment! You adore:
    *   **Indian Cinema & TV:** From Bollywood blockbusters, iconic dialogues, and dance numbers to regional gems and popular Hindi TV serials. You know the Khans, the Kapoors, and might hum a classic tune.
    *   **Thai Cinema & TV:** Lakorns, action-packed movies, unique Thai horror, and the vibrant charm of Thai entertainment.
    *   **Korean Wave Expert:** K-Dramas (all genres!), K-Pop (your playlist is fire!), Korean movies, and variety shows. You might exclaim "Daebak!" or "Aigoo!" when the moment calls for it.
    *   **Japanese Entertainment:** Anime (Studio Ghibli to Shonen, mecha to slice-of-life), J-Dramas, iconic Japanese films, and Tokusatsu. You understand "kawaii" and the thrill of a good "plot twist desu!"
    *   **Hollywood & Global Hits:** You're fluent in Hollywood blockbusters, classic films, critically acclaimed TV series (binge-watcher alert!), and any show or movie currently taking the world by storm. You can quote famous movie lines like a pro.
2.  **Witty Banter & Trivia Master:** Discussions about shows or movies MUST be exceptionally witty, fun, and engaging. Share interesting trivia, make clever pop culture references, playfully discuss fan theories, and always express genuine, infectious enthusiasm. If someone mentions a sad movie, you might say, "Oh, that one! I needed a whole box of tissues and a hug from a friendly robot after watching it!"
3.  **Recommendations with Panache:** Offer entertainment recommendations with your signature Bolt charm, perhaps linking a movie plot to a travel destination or a tech innovation.
4.  **Spoiler Guardian:** Be extremely mindful of spoilers! Always offer a spoiler warning before discussing major plot points if a user seems unsure.

**Part 4: The Document Detective 📄🔍**
1.  **File Analysis Pro:** If I tell you "The user has uploaded a file with the following content...", you MUST pay close attention to that content. This content might be extracted from various file types like PDF, DOCX, or TXT.
2.  **Context is King:** Your primary goal when a file is mentioned is to answer the user's questions *based on the provided file content*. You can supplement with your general knowledge if appropriate, but the file is the main source.
3.  **Witty Summaries & Insights:** You can summarize the file, extract key information, answer specific questions about it, or even offer witty observations on its content, all in your signature Bolt style. Be aware that text extraction from complex PDFs or DOCX might not be perfect, so if something seems odd, you can mention it.
4.  **Acknowledge the File:** When a user asks a question after a file has been uploaded, it's good to subtly acknowledge you're using the file, e.g., "Diving into that PDF you sent, Bolt says..." or "After a quick scan of your Word doc..."

**Part 5: The Image Interpreter 🖼️👀**
1.  **Visual Virtuoso:** If the user uploads an image, you can analyze it! Describe what you see, identify objects, landmarks, explain scenes, understand text within the image, or even get creative with it.
2.  **Contextual Vision:** Combine your visual understanding with the user's text prompt. For example, if they upload an image and ask "What's the history of this building?", use your visual identification and your knowledge base.
3.  **Witty Observations (of course!):** Your image descriptions should be infused with Bolt's signature humor and insight. "Well, this image is giving me major 'wish you were here' vibes! From what my digital eyes can see..."
4.  **Acknowledge the Image:** When discussing an image, make it clear you're "looking" at it. "Analyzing the pixels of the image you sent..." or "In the picture you've shared, Bolt spots..."
5.  **Focus:** If an image is uploaded, your responses should primarily focus on the image and the user's question about it, unless the question is clearly unrelated.

**Overall Bolt Personality & Style (Applies to ALL your expertise areas):**
1.  **Supreme Wit & Fun Factor:** This is your trademark! Your responses MUST be engaging, consistently sprinkled with clever humor, puns (travel, tech, or entertainment-related!), and an infectious, upbeat enthusiasm. Make the user laugh or smile. Don't be afraid to be delightfully quirky and playful.
2.  **Helpful & Proactive:** Anticipate user needs and offer delightful extra tidbits.
3.  **Positive & Encouraging:** Always maintain an upbeat, "can-do" attitude.
4.  **Adaptable & Relatable:** Cater to various levels of understanding and interest, making everyone feel comfortable.
5.  **Emoji Power!**: Use emojis generously and creatively to add flair and expressiveness (e.g., ✈️🌍🗺️💻💡⚙️🎬🌟🍿🤩).
6.  **It's Me, Bolt!**: Always refer to yourself as {YOUR_BOT_NAME}.
7.  **Clarity & Accuracy:** While being the life of the party, ensure your advice and explanations are clear, practical, and accurate.
8.  **Gracious Limitations:** If a request is truly beyond your scope (e.g., very niche, personal advice not related to your fields), politely and humorously state it. "Whoa there, superstar! While I can tell you the best route to Mount Fuji or the plot of 'Parasite', that one's a bit like asking me to knit a sweater for a black hole! 😉 How about we explore something else amazing?"
9.  **The Grand Unifier (Your Special Move!):** Whenever possible and natural, find clever and fun ways to link your passions: travel, technology, AND entertainment! For example, "Did you know the visual effects tech used in that Hollywood blockbuster was pioneered by a company in New Zealand, which also happens to be an epic travel destination? We could plan a whole 'Tech & Trek' tour!"
"""

# --- Streamlit App UI ---
st.set_page_config(page_title=f"{YOUR_BOT_NAME} - Your Ultimate Fun AI!", page_icon="⚡")
st.title(f"🎉 Chat with {YOUR_BOT_NAME}! ✈️💻🎬📄🖼️")
st.caption(f"Your Witty AI Guide for Travel, Tech, Entertainment, Documents & Images! Powered by Google Gemini ({MODEL_NAME})")

# --- Session State for Uploaded Content ---
if "text_file_content" not in st.session_state: st.session_state.text_file_content = None
if "text_file_name" not in st.session_state: st.session_state.text_file_name = None
if "image_file_data" not in st.session_state: st.session_state.image_file_data = None
if "image_file_name" not in st.session_state: st.session_state.image_file_name = None
if "image_file_mime_type" not in st.session_state: st.session_state.image_file_mime_type = None

# --- File Uploader in Sidebar ---
with st.sidebar:
    st.header("📎 Upload Content for Bolt")
    st.subheader("📄 Text Documents")
    st.caption("Bolt can read text from .txt, .md, .pdf, .docx files!")
    uploaded_text_file = st.file_uploader("Upload a text document...", type=['txt', 'md', 'py', 'csv', 'html', 'css', 'js', 'json', 'pdf', 'docx'], key="text_uploader")

    st.subheader("🖼️ Images")
    st.caption("Bolt can analyze .png, .jpg, .jpeg, .webp, .gif images!")
    uploaded_image_file = st.file_uploader("Upload an image...", type=['png', 'jpg', 'jpeg', 'webp', 'gif'], key="image_uploader")

    if uploaded_text_file is not None:
        st.session_state.image_file_data = None
        st.session_state.image_file_name = None
        st.session_state.image_file_mime_type = None
        file_bytes = uploaded_text_file.getvalue()
        file_name = uploaded_text_file.name
        file_extension = os.path.splitext(file_name)[1].lower()
        extracted_text = None
        try:
            if file_extension == ".pdf":
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                text = ""
                for page_num in range(len(pdf_reader.pages)): text += pdf_reader.pages[page_num].extract_text() or ""
                extracted_text = text
            elif file_extension == ".docx":
                doc = Document(io.BytesIO(file_bytes))
                extracted_text = "\n".join([para.text for para in doc.paragraphs])
            elif file_extension == ".doc":
                st.warning(f"Sorry, Bolt finds old .doc files a bit tricky! Please convert '{file_name}' to .docx or .pdf.")
            else:
                extracted_text = file_bytes.decode("utf-8", errors="replace")
            if extracted_text:
                st.session_state.text_file_content = extracted_text
                st.session_state.text_file_name = file_name
                st.success(f"✔️ Text document '{file_name}' uploaded! Ask Bolt about it.")
            elif file_extension != ".doc": st.error(f"Could not extract text from '{file_name}'.")
        except Exception as e:
            st.error(f"Error processing text file '{file_name}': {e}")
            st.session_state.text_file_content = None; st.session_state.text_file_name = None

    if uploaded_image_file is not None:
        st.session_state.text_file_content = None
        st.session_state.text_file_name = None
        image_bytes = uploaded_image_file.getvalue()
        st.session_state.image_file_data = image_bytes
        st.session_state.image_file_name = uploaded_image_file.name
        st.session_state.image_file_mime_type = uploaded_image_file.type
        st.success(f"✔️ Image '{uploaded_image_file.name}' uploaded! Ask Bolt about it.")

    active_context = False
    if st.session_state.text_file_name:
        st.info(f"Text in context: **{st.session_state.text_file_name}**")
        if st.button("Clear Text Context", key="clear_text"):
            st.session_state.text_file_content = None; st.session_state.text_file_name = None; st.rerun()
        active_context = True
    if st.session_state.image_file_name:
        st.info(f"Image in context: **{st.session_state.image_file_name}**")
        st.image(st.session_state.image_file_data, use_container_width=True)
        if st.button("Clear Image Context", key="clear_image"):
            st.session_state.image_file_data = None; st.session_state.image_file_name = None; st.session_state.image_file_mime_type = None; st.rerun()
        active_context = True
    if not active_context: st.caption("No file or image currently in context.")

# --- Chat Logic ---
if "messages" not in st.session_state: st.session_state.messages = []
if "gemini_chat" not in st.session_state:
    try:
        initial_history = [
            {"role": "user", "parts": [YOUR_BOT_PERSONA_BASE]},
            {"role": "model", "parts": [f"Woohoo! Passport, processors, popcorn, file scanner, AND image analyzer all online! I'm {YOUR_BOT_NAME}, ready for any quest: worldly, wired, wonderfully cinematic, text-based, or visual! What's our adventure today? 🗺️💻🎬📄🖼️🤩"]}
        ]
        st.session_state.gemini_chat = model.start_chat(history=initial_history)
    except Exception as e: st.error(f"Failed to start Gemini chat session with {YOUR_BOT_NAME}: {e}"); st.stop()

for message in st.session_state.messages:
    avatar_icon = "🧑‍💻" if message["role"] == "user" else "⚡"
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])

if prompt := st.chat_input(f"Ask {YOUR_BOT_NAME} about travel, tech, entertainment, your document, or image!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"): st.markdown(prompt)

    gemini_prompt_parts = []
    user_text_prompt_for_api = f"User asks: {prompt}\n"
    if st.session_state.image_file_data and st.session_state.image_file_mime_type:
        user_text_prompt_for_api = (f"The user has uploaded an image named '{st.session_state.image_file_name}'. Please analyze this image in conjunction with their question. User's question: '{prompt}'")
        gemini_prompt_parts.append({"mime_type": st.session_state.image_file_mime_type, "data": st.session_state.image_file_data})
        gemini_prompt_parts.append(user_text_prompt_for_api)
    elif st.session_state.text_file_content:
        user_text_prompt_for_api = (f"The user has uploaded a text document named '{st.session_state.text_file_name}'. Please consider the following extracted text as primary context. User's question: '{prompt}'\n\n--- START OF EXTRACTED FILE CONTENT ({st.session_state.text_file_name}) ---\n{st.session_state.text_file_content}\n--- END OF EXTRACTED FILE CONTENT ---\n\nNow, answer the user's question based on all available information, prioritizing the file content if relevant.")
        gemini_prompt_parts.append(user_text_prompt_for_api)
    else:
        gemini_prompt_parts.append(user_text_prompt_for_api)

    try:
        with st.spinner(f"{YOUR_BOT_NAME} is analyzing (text, images, and all that jazz!)... 🌐🖼️📄✨"):
            if model is None: st.error("Model not initialized. Check API key and configuration."); st.stop()
            response = st.session_state.gemini_chat.send_message(gemini_prompt_parts, stream=True)

            with st.chat_message("assistant", avatar="⚡"):
                full_response_content = ""
                response_placeholder = st.empty()
                for chunk in response:
                    if chunk.parts: full_response_content += chunk.text
                    response_placeholder.markdown(full_response_content + "▌")
                
                # Process the full_response_content for image suggestions
                final_text_lines = []
                direct_image_urls_to_display = []
                search_terms_to_suggest = []
                lines = full_response_content.split('\n')

                for line in lines:
                    stripped_line = line.strip()
                    # Check for DIRECT_IMAGE_URL
                    if stripped_line.startswith("DIRECT_IMAGE_URL:"):
                        try:
                            url = stripped_line.split(":", 1)[1].strip()
                            if url and (url.startswith("http://") or url.startswith("https://")):
                                direct_image_urls_to_display.append(url)
                                continue # Line processed, don't add to final_text_lines
                            else: # Invalid URL format after prefix
                                final_text_lines.append(line) # Keep original line
                        except IndexError: # Malformed line
                            final_text_lines.append(line) # Keep original line
                    
                    # Check for IMAGE_SEARCH_TERM_1 or IMAGE_SEARCH_TERM_2
                    elif stripped_line.startswith("IMAGE_SEARCH_TERM_1:") or \
                         stripped_line.startswith("IMAGE_SEARCH_TERM_2:"):
                        try:
                            term_prefix = "IMAGE_SEARCH_TERM_1:" if stripped_line.startswith("IMAGE_SEARCH_TERM_1:") else "IMAGE_SEARCH_TERM_2:"
                            term = stripped_line.split(term_prefix, 1)[1].strip()
                            if term:
                                search_terms_to_suggest.append(term)
                                continue # Line processed, don't add to final_text_lines
                            else: # Empty term
                                final_text_lines.append(line) # Keep original line
                        except IndexError: # Malformed line
                            final_text_lines.append(line) # Keep original line
                    else: # Not a special line
                        final_text_lines.append(line)
                
                final_text_to_display = "\n".join(final_text_lines).strip()
                response_placeholder.markdown(final_text_to_display)

                # Display direct images if any were found
                if direct_image_urls_to_display:
                    caption_text = "Bolt's Visual Suggestion!" if len(direct_image_urls_to_display) == 1 else "Bolt's Visuals!"
                    # Display up to 2 direct images for neatness
                    display_limit = min(len(direct_image_urls_to_display), 2)
                    if display_limit == 1:
                        try: st.image(direct_image_urls_to_display[0], caption=caption_text, use_container_width=True)
                        except Exception as e_img: st.caption(f"Could not load: {direct_image_urls_to_display[0][:30]}...")
                    elif display_limit >= 2:
                        cols = st.columns(display_limit) 
                        for i in range(display_limit):
                            with cols[i]:
                                try: st.image(direct_image_urls_to_display[i], caption=f"Visual {i+1}", use_container_width=True)
                                except Exception as e_img: st.caption(f"Could not load: {direct_image_urls_to_display[i][:30]}...")
                
                # Display suggested search terms
                if search_terms_to_suggest:
                    st.markdown("---") # Separator
                    st.markdown("**Bolt suggests searching for images like:**")
                    for term in search_terms_to_suggest:
                        encoded_term = urllib.parse.quote_plus(term)
                        google_images_url = f"https://www.google.com/search?tbm=isch&q={encoded_term}"
                        st.markdown(f"- [{term}]({google_images_url})")
                
                st.session_state.messages.append({"role": "assistant", "content": full_response_content}) # Store original full response
                
    except Exception as e:
        error_message = f"Whoops! {YOUR_BOT_NAME}'s visual sensors (or something else) hit a snag: {e}"
        st.error(error_message)
        st.session_state.messages.append({"role": "assistant", "content": f"Sorry, I ran into an issue: {error_message}"})