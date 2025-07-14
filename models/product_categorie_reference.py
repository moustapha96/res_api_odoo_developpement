


from odoo import models, fields, api, _
import re
import logging

_logger = logging.getLogger(__name__)

class CategorieReference(models.Model):
    _inherit = 'product.category'


    image = fields.Binary(string='Image', attachment=True)

    
    code = fields.Char(
        string="Code Référence Catégorie", 
        compute='_compute_code', 
        store=True, 
        readonly=True, 
        copy=False
    )
    _description = 'Référence de Catégorie de Produit'

    @api.depends('name')
    def _compute_code(self):
        """Compute category code automatically based on name"""
        for record in self:
            if record.name:
                record.code = self._generate_code(record.name)
            else:
                record.code = 'XXXX'

    def _generate_code(self, name):
        """Generate a 4-character code from category name"""
        if not name:
            return 'XXXX'
        # Remove special characters and keep only alphanumeric
        name_clean = re.sub(r'[^A-Za-z0-9]', '', name.upper())
        return name_clean[:4] if name_clean else 'XXXX'

    @api.model
    def _auto_init(self):
        """Generate codes for existing categories without codes"""
        result = super(CategorieReference, self)._auto_init()
        
        # Generate codes for existing categories that don't have one
        categories_without_code = self.search([
            '|', 
            ('code', '=', False), 
            ('code', '=', '')
        ])
        
        for category in categories_without_code:
            if category.name:
                category.code = self._generate_code(category.name)
        
        return result

    def action_regenerate_all_codes(self):
        """Action to regenerate all category codes"""
        all_categories = self.search([])
        for category in all_categories:
            if category.name:
                category.code = self._generate_code(category.name)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Codes régénérés'),
                'message': _('Tous les codes de catégories ont été régénérés avec succès.'),
                'type': 'success',
            }
        }

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    reference_auto = fields.Char(string="Référence Automatique", readonly=True, copy=False)
    extracted_model_code = fields.Char("Code Modèle (déduit)", readonly=True)
    extracted_specification = fields.Char("Spécification (déduite)", readonly=True)
    extracted_brand = fields.Char("Marque (déduite)", readonly=True)
    first_tag_code = fields.Char("Code Premier Tag", readonly=True)
    department_code = fields.Char(string="Code Département", default="E")
    

    def regenerate_all_references(self):
        """Regenerate references for all products"""
        all_products = self.search([])
        for product in all_products:
            product._onchange_compute_all_codes()
            product.generate_unique_reference()

    @api.onchange('name', 'categ_id', 'product_tag_ids','department_code')
    def _onchange_compute_all_codes(self):
        """Compute all codes when product data changes"""
        for record in self:
            # Extract brand
            record.extracted_brand = self._extract_brand(record.name)
            
            # Extract model code
            record.extracted_model_code = self._extract_model_code(record.name)
            if record.extracted_model_code:
                record.default_code = record.extracted_model_code
            
            # Extract specifications (taille, dimensions, etc.)
            record.extracted_specification = self._extract_specification(record.name)
            
            # Get first tag code
            record.first_tag_code = self._get_first_tag_code(record.product_tag_ids)
            
            # Generate automatic reference
            record._compute_reference_auto()

    def _compute_reference_auto(self):
        """Generate automatic reference with uniform notation system"""
        for record in self:
            name_part = record.name or ''
            name_upper = name_part.upper()
            
            orientation = ''
            if 'HORIZONTAL' in name_upper:
                orientation = 'H'
            elif 'VERTICAL' in name_upper:
                orientation = 'V'
                
            # Détecter si c'est un TV/Téléviseur
            is_machine_a_laver = 'MACHINE A LAVER' in name_upper or 'LAVE LINGE' in name_upper
            is_machine_a_cafe = 'MACHINE A CAFE' in name_upper or 'CAFETIERE' in name_upper
            is_tv = 'TELEVISEUR' in name_upper or 'TELEVISION' in name_upper or 'TV' in name_upper

            is_mirco = 'MICRO ONDE' in name_upper or 'MICROWAVE' in name_upper
            is_microphone = 'MICROPHONE' in name_upper
            
            # Utiliser "TV" comme catégorie pour les téléviseurs, sinon utiliser le code de catégorie normal
            if is_tv:
                category_part = 'TV'
            elif is_machine_a_cafe:
                category_part = 'MACHC'
            elif is_machine_a_laver:
                category_part = 'MACHL'
            elif is_mirco:
                category_part = 'MICRO'
            elif is_microphone:
                category_part = 'MICRP'
            else:
                category_part = record.categ_id.code if record.categ_id and record.categ_id.code else 'XXXX'

            # Take first 4 letters from cleaned name (excluding brand)
            name_without_brand = self._remove_brand_from_name(name_part, record.extracted_brand)
            
            # Special handling for TV products
            name_upper_clean = name_without_brand.upper()
            if is_tv:
                cleaned_name = 'TV'
            else:
                cleaned_name = re.sub(r'[^A-Za-z0-9]', '', name_without_brand.upper())[:4]

            # Build reference: E + Category Code + Name Part + Brand + Specification + Tag + Model
            if category_part == 'XXXX':
                ref = f"{record.department_code or 'E'}{cleaned_name}{orientation}"
            else:
                ref = f"{record.department_code or 'E'}{category_part}{orientation}"

            if record.extracted_brand:
                if record.extracted_brand.upper() in ['TELEVISEUR', 'TELEVISION']:
                    brand_code = 'TV'
                else:
                    brand_code = re.sub(r'[^A-Za-z0-9]', '', record.extracted_brand.upper())[:3]
                ref += brand_code
            elif record.first_tag_code:
                ref += record.first_tag_code

            # Add specification (taille, etc.)
            if record.extracted_specification:
                ref += record.extracted_specification

            # Add extracted model code
            if record.extracted_model_code:
                model_code_clean = re.sub(r'[^A-Za-z0-9]', '', record.extracted_model_code.upper())
                ref += model_code_clean

            record.reference_auto = ref
            record.default_code = ref

    def _extract_brand(self, name):
        """Extract brand from product name"""
        if not name:
            return False
        
        name_upper = name.upper()
        
    
        brands = [
            'SAMSUNG', 'LG', 'SONY', 'SHARP', 'TCL', 'HISENSE', 'ASTECH', 'BEKO',
            'HAIER', 'MIDEA', 'FINIX', 'WESTPOOL', 'XPER', 'SMART TECHNOLOGY','TORL',
            'TECHNOLUX', 'DESKA', 'ROCH', 'ENDURO', 'ELACTRON', 'PHILIPS',
            'NESPRESSO', 'CANDY', 'WHIRLPOOL', 'BOSCH', 'SIEMENS', 'ELECTROLUX',
            'APPLE', 'HUAWEI', 'XIAOMI', 'OPPO', 'VIVO', 'REALME', 'ONEPLUS',
            'NOKIA', 'MOTOROLA', 'HONOR', 'TECNO', 'INFINIX', 'ITEL','PANASONIC','THOMSON',
            'HISENSE', 'ASTRAL', 'ASTRALPOOL','CHANGHONG','COOCAA',
            'AQUAPOOL', 'AQUATECH','SKYWORTH',
        
            'TOSHIBA', 'HITACHI', 'DAIKIN', 'MITSUBISHI',
            # Marques manquantes ajoutées :
            'BRANDT', 'DE DIETRICH', 'MOULINEX', 'TEFAL', 'SEB',
            'SMEG', 'ARISTON', 'INDESIT', 'VESTEL', 'ARÇELIK',
            'GENERAL ELECTRIC', 'KITCHENAID', 'MAYTAG',
            'NASCO', 'BINATONE', 'BRUHM', 'SYINIX',
            'TORNADO', 'CONTINENTAL EDISON', 'SILVERCREST', 'ESSENTIEL B',
            'PROLINE', 'OCEAN', 'WANSA'
        ]
        
        # Recherche de la marque dans le nom
        for brand in brands:
            if brand in name_upper:
                return brand
        
        # Si aucune marque connue n'est trouvée, essayer d'extraire le premier mot
        words = name_upper.split()
        if words:
            first_word = words[0]
            # Vérifier si le premier mot ressemble à une marque (lettres uniquement, 3+ caractères)
            if re.match(r'^[A-Z]{3,}$', first_word):
                return first_word
        
        return False

    def _remove_brand_from_name(self, name, brand):
        """Remove brand from name to get clean product name"""
        if not brand or not name:
            return name
        
        # Supprimer la marque du nom pour obtenir le nom du produit
        name_clean = re.sub(rf'\b{re.escape(brand)}\b', '', name, flags=re.IGNORECASE)
        return name_clean.strip()

    def _extract_specification(self, name):
        """Extract specifications like size, dimensions, capacity, etc."""
        if not name:
            return False
        
        name_upper = name.upper()
        
        # Pattern for TV sizes with explicit units (42", 55", 65", etc.)
        # tv_size_pattern = r'\b(\d{2,3})\s*(?:POUCES?|INCH|")\b'
        tv_size_pattern = r'\b(\d{2,3})\b'
        tv_match = re.search(tv_size_pattern, name_upper)
        if tv_match:
            return f"{tv_match.group(1)}P"
        
        # Pattern for TV sizes without units (when context indicates TV)
        # Look for TV context words first

        # Liste de mots-clés pour détecter le contexte TV
        tv_context_words = ['TELEVISEUR', 'TELEVISION', 'TV', 'SMART TV', 'LED TV', 'OLED', 'QLED']
        is_tv_context = any(word in name_upper for word in tv_context_words)
        
        if is_tv_context:
            # AMÉLIORATION: Pattern plus simple pour détecter les tailles de TV
            # Chercher des nombres de 2-3 chiffres qui sont des tailles communes de TV
            tv_size_pattern_simple = r'\b(\d{2,3})\b'
            tv_size_matches = re.findall(tv_size_pattern_simple, name_upper)
        
            for size_str in tv_size_matches:
                size_num = int(size_str)
                # Vérifier que c'est dans la gamme des tailles de TV (24-100 pouces)
                if 24 <= size_num <= 100:
                    # Vérifier que ce n'est pas une année (2000 <= size_num <= 2030)
                    if not (2000 <= size_num <= 2030):
                        # Vérifier que ce n'est pas clairement un code modèle
                        # En cherchant le contexte autour du nombre
                        size_context_pattern = rf'\b{size_str}\b'
                        match_obj = re.search(size_context_pattern, name_upper)
                        if match_obj:
                            # Obtenir le contexte avant et après le nombre
                            start_pos = max(0, match_obj.start() - 10)
                            end_pos = min(len(name_upper), match_obj.end() + 10)
                            context = name_upper[start_pos:end_pos]
                        
                            # Si le nombre est suivi directement de 4+ lettres/chiffres, c'est probablement un code modèle
                            if not re.search(rf'\b{size_str}[A-Z0-9]{{4,}}', name_upper):
                                return f"{size_str}P"
    
        # Le reste du code reste identique...
        # Pattern for storage capacity (256GB, 1TB, etc.)
        storage_pattern = r'\b(\d+)\s*(GB|TB|GO|TO)\b'
        storage_match = re.search(storage_pattern, name_upper)
        if storage_match:
            size = storage_match.group(1)
            unit = storage_match.group(2)
            # Normalize units
            if unit in ['GO', 'GB']:
                return f"{size}G"
            elif unit in ['TO', 'TB']:
                return f"{size}T"
        
        # Pattern for RAM (8GB RAM, 16GB, etc.)
        ram_pattern = r'\b(\d+)\s*GB\s*RAM\b'
        ram_match = re.search(ram_pattern, name_upper)
        if ram_match:
            return f"{ram_match.group(1)}R"
        
        # Pattern for power/wattage (100W, 500W, etc.)
        watt_pattern = r'\b(\d+)\s*(WATT|WATTS)\b'
        watt_match = re.search(watt_pattern, name_upper)
        if watt_match:
            return f"{watt_match.group(1)}W"
                
        # Pattern for BTU (climatiseurs)
        btu_pattern = r'\b(\d+)\s*BTU\b'
        btu_match = re.search(btu_pattern, name_upper)
        if btu_match:
            btu_value = int(btu_match.group(1))
            if btu_value >= 1000:
                return f"{btu_value//1000}BTU"
            else:
                return f"{btu_value}BTU"
        
        # Pattern for capacity in liters (20L, 25L, etc.)
        liter_pattern = r'\b(\d+)\s*L(?:ITRES?)?\b'
        liter_match = re.search(liter_pattern, name_upper)
        if liter_match:
            return f"{liter_match.group(1)}L"
        
        # Pattern for weight in KG (2.5KG, 1.2kg, etc.)
        weight_pattern = r'\b(\d+(?:\.\d+)?)\s*KG\b'
        weight_match = re.search(weight_pattern, name_upper)
        if weight_match:
            weight = weight_match.group(1).replace('.', '')
            return f"{weight}K"
        
        # Pattern for dimensions (LxWxH format)
        dimension_pattern = r'\b(\d+)\s*[xX×]\s*(\d+)\s*[xX×]\s*(\d+)\b'
        dimension_match = re.search(dimension_pattern, name_upper)
        if dimension_match:
            l, w, h = dimension_match.groups()
            return f"{l}X{w}X{h}"
        
        # Pattern for CV (chevaux vapeur pour climatiseurs)
        cv_pattern = r'\b(\d+(?:\.\d+)?)\s*CV\b'
        cv_match = re.search(cv_pattern, name_upper)
        if cv_match:
            cv = cv_match.group(1).replace('.', '')
            return f"{cv}CV"
        
        # Pattern for feux (nombre de feux pour cuisinières)
        feux_pattern = r'\b(\d+)\s*FEUX\b'
        feux_match = re.search(feux_pattern, name_upper)
        if feux_match:
            return f"{feux_match.group(1)}F"
        
        # Pattern for tiroirs (réfrigérateurs)
        tiroir_pattern = r'\b(\d+)\s*T(?:IROIRS?|RS?)\b'
        tiroir_match = re.search(tiroir_pattern, name_upper)
        if tiroir_match:
            return f"{tiroir_match.group(1)}T"
        
        return False

    def _get_first_tag_code(self, tag_ids):
        """Generate code from first product tag"""
        if not tag_ids:
            return False
        
        first_tag = tag_ids[0]
        if not first_tag.name:
            return False
        
        # Clean tag name and take first 2-3 characters
        tag_clean = re.sub(r'[^A-Za-z0-9]', '', first_tag.name.upper())
        
        # Return 2-3 characters based on tag length
        if len(tag_clean) >= 4:
            return tag_clean[:3]
        elif len(tag_clean) >= 2:
            return tag_clean[:2]
        else:
            return tag_clean

    def _extract_model_code(self, name):
        """Extract model codes from product name using regex patterns - FIXED VERSION"""
        if not name:
            return False
        
        name_upper = name.upper()
        
        # Pattern 1: Codes avec espaces comme "B414 ELFM", "ABC123 XYZ"
        pattern_with_space = r'\b([A-Z]\d{2,4}\s+[A-Z]{2,6})\b'
        matches_space = re.findall(pattern_with_space, name_upper)
        
        # Pattern 2: Codes traditionnels comme "ABC123", "XYZ456" (lettres suivies de chiffres)
        # MODIFIÉ: Accepte maintenant 1 chiffre ou plus au lieu de 2 minimum
        pattern_traditional = r'\b([A-Z]{2,}\d{1,}[A-Z0-9]*)\b'
        matches_traditional = re.findall(pattern_traditional, name_upper)
        
        # Pattern 3: Codes alphanumériques complexes comme "S4NQ12JARTB" (1 lettre + chiffres + lettres)
        pattern_complex = r'\b([A-Z]\d+[A-Z0-9]{4,})\b'
        matches_complex = re.findall(pattern_complex, name_upper)
        
        # Pattern 4: Codes alphanumériques longs (6-15 chars)
        pattern_long = r'\b([A-Z0-9]{6,15})\b'
        matches_long = re.findall(pattern_long, name_upper)
        
        # Pattern 5: Codes avec tirets comme "ABC-123", "XYZ-456"
        # MODIFIÉ: Accepte maintenant 1 chiffre ou plus au lieu de 2 minimum
        pattern_dash = r'\b([A-Z]{2,}\-\d{1,}[A-Z0-9]*)\b'
        matches_dash = re.findall(pattern_dash, name_upper)
        
        # Pattern 6: Codes en fin de nom (souvent les codes modèles finaux)
        pattern_end = r'\b([A-Z0-9]{8,15})$'
        matches_end = re.findall(pattern_end, name_upper.strip())
        
        # NOUVEAU Pattern 7: Codes courts spécifiques comme "SQC1", "ABC1", etc.
        # Ce pattern capture spécifiquement les codes de 3-5 caractères avec lettres + 1-2 chiffres
        pattern_short = r'\b([A-Z]{2,4}\d{1,2})\b'
        matches_short = re.findall(pattern_short, name_upper)
        
        # NOUVEAU Pattern 8: Codes avec 1 lettre + chiffres comme "U5508", "A1234", etc.
        pattern_single_letter = r'\b([A-Z]\d{3,5})\b'
        matches_single_letter = re.findall(pattern_single_letter, name_upper)
        
        # Combiner tous les matches avec priorité
        # Prioriser les matches courts pour capturer des codes comme "SQC1" et "U5508"
        all_matches = matches_space + matches_short + matches_single_letter + matches_complex + matches_traditional + matches_end + matches_long + matches_dash
        
        # Filtrer les matches valides (contiennent lettres ET chiffres)
        valid_matches = []
        for match in all_matches:
            if re.search(r'[A-Z]', match) and re.search(r'\d', match):
                # Éviter les matches trop génériques ou qui sont des spécifications
                if not re.match(r'^\d+[A-Z]$', match):  # Éviter "7T", "55P", etc.
                    # Éviter les années
                    if not re.match(r'^(19|20)\d{2}$', match):  # Éviter "2023", "2024", etc.
                        # Éviter les BTU
                        if not re.match(r'^\d+BTU$', match):  # Éviter "12000BTU"
                            valid_matches.append(match)
    
        # Prioriser par ordre de spécificité
        if matches_space:
            return matches_space[0]
        elif matches_short:  # Codes courts comme "SQC1"
            return matches_short[0]
        elif matches_single_letter:  # NOUVEAU: Codes avec 1 lettre comme "U5508"
            return matches_single_letter[0]
        elif matches_complex:
            return matches_complex[0]
        elif matches_end:
            return matches_end[0]
        elif valid_matches:
            return valid_matches[0]
        
        return False

    @api.model
    def create(self, vals):
        """Auto-generate reference on product creation"""
        result = super(ProductTemplate, self).create(vals)
        for record in result:
            record._onchange_compute_all_codes()
        return result

    def write(self, vals):
        """Update reference when product data changes"""
        result = super(ProductTemplate, self).write(vals)
        if any(field in vals for field in ['name', 'categ_id', 'product_tag_ids','department_code']):
            for record in self:
                record._onchange_compute_all_codes()
        return result

    def generate_unique_reference(self):
        """Generate a unique reference by checking for duplicates"""
        for record in self:
            base_ref = record.reference_auto
            if not base_ref:
                record._onchange_compute_all_codes()
                base_ref = record.reference_auto
            
            # Check for duplicates and add suffix if needed
            counter = 1
            unique_ref = base_ref
            while self.search([('reference_auto', '=', unique_ref), ('id', '!=', record.id)]):
                unique_ref = f"{base_ref}{counter:02d}"
                counter += 1
            
            record.reference_auto = unique_ref

    def action_regenerate_references(self):
        """Action to regenerate all references for selected products"""
        for record in self:
            record._onchange_compute_all_codes()
            record.generate_unique_reference()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Références régénérées'),
                'message': _('Les références ont été régénérées avec succès.'),
                'type': 'success',
            }
        }

    def get_reference_breakdown(self):
        """Return a breakdown of the reference components for debugging"""
        for record in self:
            breakdown = {
                'prefix': record.department_code or 'E',
                'category': record.categ_id.code if record.categ_id else 'XXXX',
                'product_name': re.sub(r'[^A-Za-z0-9]', '', 
                    self._remove_brand_from_name(record.name or '', record.extracted_brand).upper())[:4],
                'brand': record.extracted_brand,
                'specification': record.extracted_specification,
                'tag': record.first_tag_code,
                'model': record.extracted_model_code,
                'final_reference': record.reference_auto
            }
            _logger.info(f"Reference breakdown for {record.name}: {breakdown}")
            return breakdown



