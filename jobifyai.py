from openai import OpenAI
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_key = os.getenv('OPENAI_API_KEY')
if api_key is None:
    print("OPENAI_API_KEY is not set.")

client = OpenAI(api_key=api_key)

MODEL="gpt-4o-mini"

def process_gpt_4o_turbo(text, agent):
    try:
        completion = client.chat.completions.create(
        model=MODEL,
        messages=[
                {"role": "system", "content": agent},
                {"role": "user", "content": text},
            ],
            temperature=0.5,
            max_tokens=4096,
            n=1,
            stop=None,
        )
        print(completion.choices[0].message.content)
        logger.info(f"completion.choices[0].message.content : {completion.choices[0].message.content}")
        completion_text = completion.choices[0].message.content
        if "```json" in completion_text and "```" in completion_text:
            json_content = completion_text.split("```json")[1].split("```")[0].strip()
        else:
            json_content = completion_text.strip()

        completion_json = json_content
        
        return completion_json
    except json.JSONDecodeError:
        print({"error": "Invalid JSON response from GPT-4o"})
        logger.error("error : Invalid JSON response from GPT-4o")  
    except KeyError:
        print({"error": "Error processing completion."})
        logger.error("error""Error processing completion.")
    except Exception as e:
        print({"error": f"An error occurred: {e}"})
        logger.error(f"error An error occurred: {e}")
