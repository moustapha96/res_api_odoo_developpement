import requests

# Configuration
base_url = "http://your_odoo_server"
headers = {"Content-Type": "application/json"}

def send_interactive_message(to, message, buttons):
    data = {
        "to": to,
        "message": message,
        "buttons": buttons
    }
    response = requests.post(f"{base_url}/api/whatsapp/send_interactive", headers=headers, json=data)
    return response.json()

# Envoi des options de rendez-vous
customer_phone = "33612345678"
appointment_message = "Choisissez une date pour votre rendez-vous :"
appointment_buttons = [
    {"type": "reply", "reply": {"id": "apt_monday", "title": "Lundi 10/07"}},
    {"type": "reply", "reply": {"id": "apt_tuesday", "title": "Mardi 11/07"}},
    {"type": "reply", "reply": {"id": "apt_wednesday", "title": "Mercredi 12/07"}},
    {"type": "reply", "reply": {"id": "apt_thursday", "title": "Jeudi 13/07"}}
]

result = send_interactive_message(customer_phone, appointment_message, appointment_buttons)
print("Résultat de l'envoi des options de rendez-vous:", result)

# Traitement de la sélection de date (dans le webhook)
def process_appointment_selection(webhook_data):
    messages = webhook_data['entry'][0]['changes'][0]['value']['messages']
    for message in messages:
        if message['type'] == 'interactive':
            button_reply = message['interactive']['button_reply']
            customer_phone = message['from']
            appointment_id = button_reply['id']
            appointment_date = button_reply['title']
            
            # Enregistrez le rendez-vous dans votre système
            book_appointment(customer_phone, appointment_id, appointment_date)
            
            # Envoyez un message de confirmation
            confirmation_message = f"Votre rendez-vous est confirmé pour le {appointment_date}. Voulez-vous un rappel ?"
            reminder_buttons = [
                {"type": "reply", "reply": {"id": "reminder_yes", "title": "Oui, rappel 24h avant"}},
                {"type": "reply", "reply": {"id": "reminder_no", "title": "Non, merci"}}
            ]
            send_interactive_message(customer_phone, confirmation_message, reminder_buttons)

def book_appointment(customer_phone, appointment_id, appointment_date):
    # Implémentez ici la logique pour enregistrer le rendez-vous dans votre système Odoo
    print(f"Rendez-vous enregistré pour le client {customer_phone}: {appointment_date} ({appointment_id})")

# Exemple de données de webhook
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
                            "id": "apt_monday",
                            "title": "Lundi 10/07"
                        }
                    }
                }]
            }
        }]
    }]
}

# Simuler le traitement de la sélection de rendez-vous
process_appointment_selection(webhook_data)