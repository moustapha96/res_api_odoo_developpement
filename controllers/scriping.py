from odoo import http
from odoo.http import request
import json
import requests
from bs4 import BeautifulSoup
import werkzeug.wrappers

class ScraperController(http.Controller):

    @http.route('/api/getText', methods=['GET'], type='http', auth='none', cors="*")
    def get_texte(self, **kwargs):
        target_url = kwargs.get('target_url')
    
        response = requests.get(target_url, timeout=10)
        response.raise_for_status()  # Vérifie les erreurs HTTP
        soup = BeautifulSoup(response.text, 'html.parser')

        short_description  = soup.select_one(".woocommerce-product-details__short-description").text.strip()
        gallery_images = []
        
        gallery_elements = soup.select(".woocommerce-product-gallery__image img")
        for img in gallery_elements:
            img_url = img.get("data-large_image") or img.get("src")
            if img_url:
                gallery_images.append(img_url)
        
        category_elem = soup.select_one(".posted_in a")
        category = category_elem.get_text(strip=True) if category_elem else "Catégorie non trouvée."

        result = {
            "description": short_description,
            "images": gallery_images,
            "categorie": category
        }

        return werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
            response=json.dumps(result)
        )

      

    

    @http.route('/api/scrape_productsA', methods=['GET'], type='http', auth='none', cors="*")
    def api_scrape_productsA(self, **kwargs):
        """
        API pour scraper les produits d'un site WooCommerce.
        URL cible : doit être passée en paramètre `target_url`.
        """
        # URL cible à scraper (passée dans les paramètres GET)
        target_url = kwargs.get('target_url')
        if not target_url:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({"error": "Veuillez fournir l'URL cible via le paramètre 'target_url'."})
            )

        try:
            # Envoi de la requête HTTP
            response = requests.get(target_url, timeout=10)
            response.raise_for_status()  # Vérifie les erreurs HTTP
            soup = BeautifulSoup(response.text, 'html.parser')

            # Trouver tous les produits
            products = soup.select("ul.products li.product")
            product_data = []

            # Extraire les informations des produits
            for product in products:
                title = product.select_one("h2.woocommerce-loop-product__title").text.strip() if product.select_one("h2.woocommerce-loop-product__title") else None
                link = product.select_one("a.woocommerce-LoopProduct-link")["href"] if product.select_one("a.woocommerce-LoopProduct-link") else None
                image = product.select_one("img")["src"] if product.select_one("img") else None
                category = [cls for cls in product.get("class", []) if cls.startswith("product_cat-")]
                tags = [cls for cls in product.get("class", []) if cls.startswith("product_tag-")]
                description = product.select_one("img")["alt"].strip() if product.select_one("img") and product.select_one("img").get("alt") else None

                # Ajouter les informations du produit
                product_data.append({
                    "title": title,
                    "link": link,
                    "image": image,
                    "category": category[0] if category else None,
                    "tags": tags[0] if tags else None,
                    "description": description
                })

            # Organiser les données
            page_data = {
                "url": target_url,
                "products": product_data
            }

            # Retourner les données au format JSON
            return werkzeug.wrappers.Response(
                status=200,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps(page_data, ensure_ascii=False, indent=4)
            )
        except requests.exceptions.RequestException as e:
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({"error": f"Erreur lors de la requête : {str(e)}"})
            )
        except Exception as e:
            return werkzeug.wrappers.Response(
                status=500,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({"error": f"Erreur inconnue : {str(e)}"})
            )
