import requests

# Configuration
base_url = "http://your_odoo_server"
headers = {"Content-Type": "application/json"}

# Fonction pour envoyer le message interactif
def send_interactive_message(to, message, buttons):
    data = {
        "to": to,
        "message": message,
        "buttons": buttons
    }
    response = requests.post(f"{base_url}/api/whatsapp/send_interactive", headers=headers, json=data)
    return response.json()

# Envoi du message d'enquête
customer_phone = "33612345678"
survey_message = "Comment évalueriez-vous votre expérience récente avec notre service client ?"
survey_buttons = [
    {"type": "reply", "reply": {"id": "rating_excellent", "title": "Excellent"}},
    {"type": "reply", "reply": {"id": "rating_good", "title": "Bon"}},
    {"type": "reply", "reply": {"id": "rating_average", "title": "Moyen"}},
    {"type": "reply", "reply": {"id": "rating_poor", "title": "Mauvais"}}
]

result = send_interactive_message(customer_phone, survey_message, survey_buttons)
print("Résultat de l'envoi de l'enquête:", result)

# Traitement de la réponse (dans le webhook)
def process_survey_response(webhook_data):
    messages = webhook_data['entry'][0]['changes'][0]['value']['messages']
    for message in messages:
        if message['type'] == 'interactive':
            button_reply = message['interactive']['button_reply']
            customer_phone = message['from']
            rating_id = button_reply['id']
            rating_title = button_reply['title']
            
            # Enregistrez la réponse dans votre système
            save_customer_rating(customer_phone, rating_id, rating_title)
            
            # Envoyez un message de remerciement
            thank_you_message = f"Merci pour votre retour ! Vous avez évalué notre service comme étant {rating_title}."
            send_interactive_message(customer_phone, thank_you_message, [])

def save_customer_rating(customer_phone, rating_id, rating_title):
    # Implémentez ici la logique pour sauvegarder la note dans votre système Odoo
    print(f"Enregistrement de la note du client {customer_phone}: {rating_title} ({rating_id})")

# Exemple de données de webhook (à utiliser dans votre gestionnaire de webhook)
webhook_data = {
    "object": "whatsapp_business_account",
    "entry": [{
        "changes": [{
            "value": {
                "messages": [{
                    "from": "33612345678",
                    "type": "interactive",
                    "interactive": {
                        "type": "button_reply",
                        "button_reply": {
                            "id": "rating_good",
                            "title": "Bon"
                        }
                    }
                }]
            }
        }]
    }]
}

# Simuler le traitement de la réponse
process_survey_response(webhook_data)