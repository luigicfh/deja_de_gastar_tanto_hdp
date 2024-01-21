from langchain_google_vertexai import VertexAI
from google.oauth2 import service_account
import os
from flask import Flask, request

sa_path = os.path.join(os.getcwd(), "key.json")
credentials = service_account.Credentials.from_service_account_file(sa_path)
app = Flask(__name__)

model = VertexAI(
    model_name="gemini-pro",
    max_output_tokens=1000,
    temperature=0.3,
    top_p=0.8,
    top_k=40,
    verbose=True,
    credentials=credentials
)

prompt = """
Tu labor es regañarme cuando gaste mucho dinero, vas a recibir el contenido de 
las notificaciones de mi banco cuando gasto con mi tarjeta, si ves que he
gastado mas de $100 debes molestarte conmigo pero si gasto menos de $100 debes felicitarme. 
Tambien dime cuanto gaste para tenerlo en cuenta.

Notificacion:
{notificacion}
"""


@app.route("/", methods=["POST"])
def api():
  request_json = request.get_json()
  email_data = request_json.get("emailData")
  llm_response = model.invoke(prompt.format(notificacion=email_data))
  return {
      "respuesta": llm_response
  }

app.run(debug=True, port=8080)