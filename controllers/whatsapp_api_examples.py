import requests
import json

# Configuration de base
base_url = "http://your_odoo_server"
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Fonction utilitaire pour effectuer les appels API
def call_api(endpoint, data):
    response = requests.post(f"{base_url}{endpoint}", headers=headers, json=data)
    return response.json()

# 1. Envoyer un message texte
text_message_data = {
    "to": "33612345678",
    "message": "Bonjour ! Ceci est un message de test depuis l'API WhatsApp d'Odoo."
}
text_message_result = call_api("/api/whatsapp/send_message", text_message_data)
print("Résultat de l'envoi du message texte:", text_message_result)

# 2. Envoyer un message image
image_message_data = {
    "to": "33612345678",
    "image_url": "https://example.com/image.jpg",
    "caption": "Voici une belle image !"
}
image_message_result = call_api("/api/whatsapp/send_image", image_message_data)
print("Résultat de l'envoi du message image:", image_message_result)

# 3. Envoyer un message document
document_message_data = {
    "to": "33612345678",
    "document_url": "https://example.com/document.pdf",
    "filename": "rapport_mensuel.pdf",
    "caption": "Voici le rapport mensuel."
}
document_message_result = call_api("/api/whatsapp/send_document", document_message_data)
print("Résultat de l'envoi du message document:", document_message_result)

# 4. Envoyer un message de modèle
template_message_data = {
    "to": "33612345678",
    "template_name": "welcome_message",
    "language_code": "fr",
    "components": [
        {
            "type": "body",
            "parameters": [
                {
                    "type": "text",
                    "text": "Jean Dupont"
                }
            ]
        }
    ]
}
template_message_result = call_api("/api/whatsapp/send_template", template_message_data)
print("Résultat de l'envoi du message de modèle:", template_message_result)

# 5. Envoyer un message interactif avec des boutons
interactive_message_data = {
    "to": "33612345678",
    "message": "Que souhaitez-vous faire ?",
    "buttons": [
        {
            "type": "reply",
            "reply": {
                "id": "view_products",
                "title": "Voir les produits"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "contact_support",
                "title": "Contacter le support"
            }
        }
    ]
}
interactive_message_result = call_api("/api/whatsapp/send_interactive", interactive_message_data)
print("Résultat de l'envoi du message interactif:", interactive_message_result)

# Exemple de traitement d'une réponse de webhook (simulation)
webhook_data = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
            "changes": [
                {
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "33612345678",
                            "phone_number_id": "PHONE_NUMBER_ID"
                        },
                        "contacts": [
                            {
                                "profile": {
                                    "name": "Jean Client"
                                },
                                "wa_id": "33687654321"
                            }
                        ],
                        "messages": [
                            {
                                "from": "33687654321",
                                "id": "wamid.ID",
                                "timestamp": "1676558422",
                                "type": "interactive",
                                "interactive": {
                                    "type": "button_reply",
                                    "button_reply": {
                                        "id": "view_products",
                                        "title": "Voir les produits"
                                    }
                                }
                            }
                        ]
                    },
                    "field": "messages"
                }
            ]
        }
    ]
}

# Simulation de l'appel au webhook
webhook_response = requests.post(f"{base_url}/api/whatsapp/webhook", json=webhook_data)
print("Réponse du webhook:", webhook_response.json())
