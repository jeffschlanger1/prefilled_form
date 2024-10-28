import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import openai
from openai import OpenAI
import os
import json
import urllib.parse

# Load environment variables
load_dotenv()

# Set OpenAI API key from the .env file
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# form_url = os.getenv("form_url")
form_url = st.secrets["form_url"]

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def extract_fields_with_openai(text):
    # Define the prompt to extract the fields
    prompt = f"""
    Extract the following fields from the text and provide the output in JSON format:
    - Agency
    - Case #
    - Occurred
    - Location
    - Officer
    - Exact Time
    - Written by
    
    Here is the document text:
    {text}
    """
    
    # Call OpenAI Chat API to extract the fields
    response = client.chat.completions.create(
        model="gpt-4",  # or "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts fields from text."},
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the OpenAI response
    extracted_data = response.choices[0].message.content
    
    return extracted_data

def summarize_text_with_openai(text):
    # Define the prompt to summarize the text
    prompt = f"""
    Please summarize the following text in a concise manner:
    
    {text}
    """
    
    # Call OpenAI Chat API for summarization
    response = client.chat.completions.create(
        model="gpt-4",  # or "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": "You are an expert at summarizing text."},
            {"role": "user", "content": prompt}
        ]
    )
    
    # Get the summary from the response
    summary = response.choices[0].message.content.strip()
    
    return summary

def generate_prefilled_url(form_url, extracted_data, summary):
    # Map the extracted data fields to Google Form entry IDs
    prefill_data = {
        "entry.1941630927": match_radio_option(extracted_data.get("Agency", "")),
        "entry.1124423131": extracted_data.get("Case #", ""),
        "entry.185129316": extracted_data.get("Occurred", ""),
        "entry.185415823": extracted_data.get("Location", ""),
        "entry.961768524": extracted_data.get("Exact Time", ""),
        # "entry.4444444444": extracted_data.get("Age/Race/Gender", ""),
        "entry.1382641879": summary  # Adding summary to form
    }

    # Encode the prefilled data into URL parameters
    prefilled_url = form_url + "?" + urllib.parse.urlencode(prefill_data)
    
    return prefilled_url

def match_radio_option(value):
    # This function will match the extracted value to an available radio button option in the form
    radio_button_options = {
        "Aurora Police Department": "Aurora Police Department",
        "Petaluma Police Department": "Petaluma Police Department",
        "San Leandro Police Department": "San Leandro Police Department",
        "DHS-CRCL": "DHS-CRCL",
        "NYAG": "NYAG"
        # Add other available options for the radio button here
    }
    
    # Return the corresponding Google Form option text if found, otherwise return empty
    return radio_button_options.get(value, "")

def main():
    st.set_page_config(page_title="PDF Field Extractor and Prefill Form", page_icon=":page_with_curl:")
    st.header("Extract Fields, Generate Summary, and Prefill Google Form using OpenAI :books:")

    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader(
            "Upload your PDFs here and click on 'Process'", accept_multiple_files=True)

        if st.button("Process"):
            with st.spinner("Processing"):
                # Extract PDF text
                raw_text = get_pdf_text(pdf_docs)

                # Extract relevant fields using OpenAI
                extracted_data = extract_fields_with_openai(raw_text)

                # Generate and display summary of the text
                summary = summarize_text_with_openai(raw_text)

                # Display the extracted data as JSON
                st.subheader("Extracted Data")
                try:
                    extracted_json = json.loads(extracted_data)
                    st.json(extracted_json)

                    # Generate the prefilled Google Form URL
                    form_url = form_url
                    prefilled_url = generate_prefilled_url(form_url, extracted_json, summary)
                    
                    st.subheader("Prefilled Google Form URL")
                    st.write(prefilled_url)
                    st.markdown(f"[Click here to fill the form]({prefilled_url})")

                except json.JSONDecodeError:
                    st.error("Failed to parse OpenAI response as JSON. Here's the raw response:")
                    st.text(extracted_data)

if __name__ == '__main__':
    main()
