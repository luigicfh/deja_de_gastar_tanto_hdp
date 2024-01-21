import os
import imaplib
import email
from dotenv import load_dotenv
import re
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_openai import ChatOpenAI
import requests


load_dotenv()
chat = ChatOpenAI(
    temperature=0.3, openai_api_key=os.environ.get("KEY"), max_tokens=1000
)


def extract_text_from_html(html_string):
    text = re.sub(r"<style[^>]*>.*?</style>", "", html_string, flags=re.DOTALL)
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"\n", " ", text)
    text = re.sub(r"&[a-zA-Z0-9]+;", lambda m: m.group(0), text)
    text = text.strip()
    return text


def get_email_body(email_message):
    if email_message.is_multipart():
        for part in email_message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition")).lower()
            if (
                content_type in ["text/plain", "text/html"]
                and "attachment" not in content_disposition
            ):
                body = part.get_payload(decode=True).decode()
                return extract_text_from_html(body)
    else:
        return email_message.get_payload(decode=True).decode()


def fetch_last_expense_email():
    imap_server = "imap.gmail.com"
    username = os.environ.get("username")
    password = os.environ.get("password")
    try:
        mail = imaplib.IMAP4_SSL(imap_server, port=993)
        mail.login(username, password)
        mail.select("promerica")
        status, data = mail.search(None, "ALL")
        if status == "OK":
            mail_ids = data[0].split()
            latest_mail_id = mail_ids[0]
            status, data = mail.fetch(latest_mail_id, "(RFC822)")
            raw_email = data[0][1]
            email_message = email.message_from_bytes(raw_email)
            return get_email_body(email_message)
        else:
            print("No matching emails found.")
    except Exception as e:
        raise Exception(e)
    finally:
        mail.logout()


if __name__ == "__main__":
    notification = fetch_last_expense_email()
    template = """Tu labor es regañarme cuando gaste mucho dinero, vas a recibir el contenido de 
    las notificaciones de mi banco cuando gasto con mi tarjeta, si ves que he
    gastado mas de {max_gasto} debes molestarte conmigo y debes ser ofensivo como un general del ejercito, 
    pero si gasto menos de {min_gasto} debes felicitarme. Tambien dime cuanto gaste para tenerlo en cuenta.
    
    Notificacion:
    {notificacion}
    """
    system_message_prompt = SystemMessagePromptTemplate.from_template(template)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt])
    response = chat.invoke(
        chat_prompt.format_prompt(
            max_gasto="$100",
            min_gasto="$100",
            notificacion=notification,
        ).to_messages()
    )
    url = f"https://api.telegram.org/bot{os.environ.get('T_TOKEN')}/sendMessage?chat_id={os.environ.get('CHAT_ID')}&text={response.content}"
    requests.get(url)
