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

# Envoi du menu
customer_phone = "33612345678"
menu_message = "Bienvenue chez Pizza Express ! Que souhaitez-vous commander ?"
menu_buttons = [
    {"type": "reply", "reply": {"id": "order_margherita", "title": "Pizza Margherita"}},
    {"type": "reply", "reply": {"id": "order_pepperoni", "title": "Pizza Pepperoni"}},
    {"type": "reply", "reply": {"id": "order_vegetarian", "title": "Pizza Végétarienne"}},
    {"type": "reply", "reply": {"id": "view_full_menu", "title": "Voir le menu complet"}}
]

result = send_interactive_message(customer_phone, menu_message, menu_buttons)
print("Résultat de l'envoi du menu:", result)

# Traitement de la commande (dans le webhook)
def process_order(webhook_data):
    messages = webhook_data['entry'][0]['changes'][0]['value']['messages']
    for message in messages:
        if message['type'] == 'interactive':
            button_reply = message['interactive']['button_reply']
            customer_phone = message['from']
            order_id = button_reply['id']
            order_item = button_reply['title']
            
            if order_id == "view_full_menu":
                send_full_menu(customer_phone)
            else:
                place_order(customer_phone, order_id, order_item)

def send_full_menu(customer_phone):
    # Implémentez ici la logique pour envoyer le menu complet
    full_menu_message = "Voici notre menu complet : [...]"
    send_interactive_message(customer_phone, full_menu_message, [])

def place_order(customer_phone, order_id, order_item):
    # Implémentez ici la logique pour enregistrer la commande dans votre système Odoo
    print(f"Nouvelle commande du client {customer_phone}: {order_item} ({order_id})")
    confirmation_message = f"Merci pour votre commande ! Votre {order_item} sera prête dans 30 minutes."
    send_interactive_message(customer_phone, confirmation_message, [])

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
                            "id": "order_margherita",
                            "title": "Pizza Margherita"
                        }
                    }
                }]
            }
        }]
    }]
}

# Simuler le traitement de la commande
process_order(webhook_data)