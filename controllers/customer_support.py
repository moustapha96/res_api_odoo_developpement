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

# Envoi des options de support
customer_phone = "33612345678"
support_message = "Bonjour ! Pour quel type de problème avez-vous besoin d'aide ?"
support_buttons = [
    {"type": "reply", "reply": {"id": "issue_technical", "title": "Problème technique"}},
    {"type": "reply", "reply": {"id": "issue_billing", "title": "Facturation"}},
    {"type": "reply", "reply": {"id": "issue_delivery", "title": "Livraison"}},
    {"type": "reply", "reply": {"id": "issue_other", "title": "Autre"}}
]

result = send_interactive_message(customer_phone, support_message, support_buttons)
print("Résultat de l'envoi des options de support:", result)

# Traitement de la sélection du problème (dans le webhook)
def process_support_request(webhook_data):
    messages = webhook_data['entry'][0]['changes'][0]['value']['messages']
    for message in messages:
        if message['type'] == 'interactive':
            button_reply = message['interactive']['button_reply']
            customer_phone = message['from']
            issue_id = button_reply['id']
            issue_type = button_reply['title']
            
            # Créez un ticket de support dans votre système
            create_support_ticket(customer_phone, issue_id, issue_type)
            
            # Envoyez un message de confirmation et les prochaines étapes
            if issue_id == "issue_technical":
                next_steps = "Un technicien va vous contacter dans les prochaines 2 heures. En attendant, avez-vous essayé de redémarrer l'appareil ?"
            elif issue_id == "issue_billing":
                next_steps = "Notre service de facturation va examiner votre compte et vous recontacter dans les 24 heures. Pouvez-vous nous donner le numéro de la facture concernée ?"
            elif issue_id == "issue_delivery":
                next_steps = "Nous allons vérifier le statut de votre livraison. Pouvez-vous nous fournir votre numéro de commande ?"
            else:
                next_steps = "Un agent va prendre en charge votre demande dans les plus brefs délais. Pouvez-vous nous donner plus de détails sur votre problème ?"
            
            send_interactive_message(customer_phone, next_steps, [])

def create_support_ticket(customer_phone, issue_id, issue_type):
    # Implémentez ici la logique pour créer un ticket de support dans votre système Odoo
    print(f"Ticket de support créé pour le client {customer_phone}: {issue_type} ({issue_id})")

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
                            "id": "issue_technical",
                            "title": "Problème technique"
                        }
                    }
                }]
            }
        }]
    }]
}

# Simuler le traitement de la demande de support
process_support_request(webhook_data)