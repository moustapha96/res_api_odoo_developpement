from odoo import http
from odoo.http import request
import json
import requests
from bs4 import BeautifulSoup
import werkzeug.wrappers

import os
import datetime
import urllib.parse
from pathlib import Path

class ScraperController(http.Controller):



    @http.route('/api/scrape_products_full', methods=['GET'], type='http', auth='none', cors="*")
    def scrape_products_full(self, **kwargs):
        target_url = kwargs.get('target_url')
        fetch_details = kwargs.get('fetch_details', 'false').lower() == 'true'
        save_to_file = kwargs.get('save_to_file', 'true').lower() == 'true'

        if not target_url:
            return werkzeug.wrappers.Response(
                status=400,
                content_type='application/json; charset=utf-8',
                headers=[('Cache-Control', 'no-store'), ('Pragma', 'no-cache')],
                response=json.dumps({"error": "Veuillez fournir l'URL cible via le paramètre 'target_url'."})
            )

        try:
            response = requests.get(target_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            products = soup.select("ul.products li.product")
            product_data = []

            for product in products:
                title = product.select_one("h2.woocommerce-loop-product__title")
                link = product.select_one("a.woocommerce-LoopProduct-link")
                image = product.select_one("img")
                title_text = title.text.replace('  ', ' ') 

                product_info = {
                    "title": title_text.strip() if title else None,
                    "link": link["href"] if link else None,
                    "image" : image.get("src") if image else None,
                }


                # Détails du produit
                if fetch_details and product_info["link"]:
                    try:
                        details_produits = self.fetch_page_text(target_url=product_info["link"])
                        # product_info["details"] = details_produits
                        product_info["summary_text"] = details_produits.get("summary_text", None)
                        product_info["images"] = details_produits.get("images", [])
                        product_info["categories"] = details_produits.get("categories", [])
                        product_info["tags"] = details_produits.get("tags", [])

                    except Exception as e:
                        product_info["detail_fetch_error"] = str(e)

                product_data.append(product_info)

            page_data = {
                "url": target_url,
                "scrape_date": datetime.datetime.now().isoformat(),
                "produits_nbre": len(product_data),
                "produits": product_data
            }

            # je veux verifier les produits qui existe ou pas dans la base de donnee
            product_ids = request.env['product.template'].sudo().search([('name', 'in', [p['title'] for p in product_data])]).ids
            for product in product_data:
                if product['title'] in product_ids:
                    product['exists_in_db'] = True
                else:
                    product['exists_in_db'] = False


            file_path = None
            if save_to_file:
                data_dir = os.path.join(os.path.dirname(__file__), '../data')
                os.makedirs(data_dir, exist_ok=True)

                domain = urllib.parse.urlparse(target_url).netloc.replace('.', '_')
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"products_{domain}_{timestamp}.json"
                file_path = os.path.join(data_dir, filename)

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(page_data, f, ensure_ascii=False, indent=4)

                page_data["file_saved"] = file_path

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




    def fetch_page_text(self,target_url):
        """Fetches the text from a specific section of a webpage."""
        if not target_url:
            return {
                "error": "Veuillez fournir l'URL cible via le paramètre 'target_url'."
            }

        try:
            response = requests.get(target_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extraire le texte de la section spécifique
            summary_section = soup.select_one('div.summary.entry-summary')
            if not summary_section:
                return {
                    "error": "La section spécifiée n'a pas été trouvée."
                }

            # Extraire le titre
            title_element = summary_section.select_one('h1.product_title.entry-title')
            title_text = title_element.get_text(strip=True) if title_element else "Titre non trouvé"

            # Extraire la description courte
            description_section = summary_section.select_one('div.woocommerce-product-details__short-description')
            if description_section:
                paragraphs = description_section.find_all('p')
                summary_text = "\n".join(p.get_text(strip=True) for p in paragraphs)
            else:
                summary_text = summary_section.get_text(separator='\n', strip=True)

            # Extraire les images de la galerie
            gallery_section = soup.select_one('div.woocommerce-product-gallery')
            images = []
            if gallery_section:
                for img in gallery_section.select('div.woocommerce-product-gallery__image img'):
                    images.append({
                        "src": img.get("data-large_image") or img.get("src")
                    })

            # Extraire la catégorie et les tags
            category_element = summary_section.select_one('span.posted_in')
            categories = [a.get_text(strip=True) for a in category_element.select('a')] if category_element else []

            tag_element = summary_section.select_one('span.tagged_as')
            tags = [a.get_text(strip=True) for a in tag_element.select('a')] if tag_element else []

            page_data = {
                "title": title_text,
                "summary_text": summary_text,
                "images": images,
                "categories": categories,
                "tags": tags
            }

            return page_data

        except requests.exceptions.RequestException as e:
            return {
                "error": f"Erreur lors de la requête : {str(e)}"
            }
        except Exception as e:
            return {
                "error": f"Erreur inconnue : {str(e)}"
            }
