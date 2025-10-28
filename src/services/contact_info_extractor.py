"""
Extractor de información de contacto.
Implementa IContactInfoExtractor siguiendo SRP.
"""
from typing import Dict, Any, Optional
import re
import phonenumbers
from email_validator import validate_email, EmailNotValidError

from ..interfaces import IContactInfoExtractor, ILogger
from ..utils.logger import Logger


class ContactInfoExtractor(IContactInfoExtractor):
    """Servicio para extraer y validar información de contacto de datos de negocios."""

    def __init__(self, logger: ILogger = None):
        self._logger = logger or Logger()

        # Patrones de regex para extracción
        self._phone_patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890, 123-456-7890, 123.456.7890
            r'\d{10}',  # 1234567890
            r'\+\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # +1-123-456-7890
        ]

        self._email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        # Palabras clave para identificar campos de contacto
        self._contact_keywords = {
            'phone': ['phone', 'telephone', 'tel', 'mobile', 'cell', 'contact'],
            'email': ['email', 'e-mail', 'mail', 'contact'],
            'website': ['website', 'web', 'url', 'site', 'homepage']
        }

    def extract_contacts(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae información de contacto de los datos del negocio.

        Args:
            business_data: Diccionario con datos del negocio

        Returns:
            Diccionario con información de contacto extraída
        """
        self._logger.debug(f"Extrayendo contactos para: {business_data.get('name', 'Unknown')}")

        contact_info = {
            'phone': None,
            'email': None,
            'website': None,
            'contact_score': 0
        }

        try:
            # Extraer teléfono
            contact_info['phone'] = self._extract_phone(business_data)

            # Extraer email
            contact_info['email'] = self._extract_email(business_data)

            # Extraer website
            contact_info['website'] = self._extract_website(business_data)

            # Calcular score de contacto
            contact_info['contact_score'] = self._calculate_contact_score(contact_info)

            self._logger.debug(f"Contactos extraídos - Teléfono: {contact_info['phone']}, "
                             f"Email: {contact_info['email']}, Website: {contact_info['website']}")

        except Exception as e:
            self._logger.warning(f"Error extrayendo contactos: {e}")

        return contact_info

    def validate_contact_info(self, contact_info: Dict[str, Any]) -> bool:
        """
        Valida que la información de contacto sea válida.

        Args:
            contact_info: Diccionario con información de contacto

        Returns:
            True si tiene al menos un contacto válido
        """
        phone = contact_info.get('phone')
        email = contact_info.get('email')
        website = contact_info.get('website')

        # Validar teléfono
        phone_valid = phone and self._validate_phone(phone)

        # Validar email
        email_valid = email and self._validate_email(email)

        # Validar website
        website_valid = website and self._validate_website(website)

        # Al menos un contacto válido
        is_valid = phone_valid or email_valid or website_valid

        if not is_valid:
            self._logger.debug("Información de contacto no válida - "
                             f"Teléfono válido: {phone_valid}, Email válido: {email_valid}, "
                             f"Website válido: {website_valid}")

        return is_valid

    def _extract_phone(self, business_data: Dict[str, Any]) -> Optional[str]:
        """Extrae número de teléfono de los datos del negocio."""
        # Buscar en campos específicos
        for field_name, value in business_data.items():
            field_lower = field_name.lower()

            # Verificar si el campo es de teléfono
            if any(keyword in field_lower for keyword in self._contact_keywords['phone']):
                phone = self._extract_phone_from_text(str(value))
                if phone:
                    return phone

        # Buscar en todos los campos de texto
        for value in business_data.values():
            if isinstance(value, str):
                phone = self._extract_phone_from_text(value)
                if phone:
                    return phone

        return None

    def _extract_email(self, business_data: Dict[str, Any]) -> Optional[str]:
        """Extrae dirección de email de los datos del negocio."""
        # Buscar en campos específicos
        for field_name, value in business_data.items():
            field_lower = field_name.lower()

            # Verificar si el campo es de email
            if any(keyword in field_lower for keyword in self._contact_keywords['email']):
                email = self._extract_email_from_text(str(value))
                if email:
                    return email

        # Buscar en todos los campos de texto
        for value in business_data.values():
            if isinstance(value, str):
                email = self._extract_email_from_text(value)
                if email:
                    return email

        return None

    def _extract_website(self, business_data: Dict[str, Any]) -> Optional[str]:
        """Extrae URL del website de los datos del negocio."""
        # Buscar en campos específicos
        for field_name, value in business_data.items():
            field_lower = field_name.lower()

            # Verificar si el campo es de website
            if any(keyword in field_lower for keyword in self._contact_keywords['website']):
                website = self._normalize_website(str(value))
                if website:
                    return website

        # Buscar en todos los campos de texto
        for value in business_data.values():
            if isinstance(value, str):
                website = self._normalize_website(value)
                if website:
                    return website

        return None

    def _extract_phone_from_text(self, text: str) -> Optional[str]:
        """Extrae número de teléfono de un texto usando patrones regex."""
        for pattern in self._phone_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Limpiar y validar el número encontrado
                clean_phone = self._clean_phone_number(match)
                if self._validate_phone(clean_phone):
                    return clean_phone
        return None

    def _extract_email_from_text(self, text: str) -> Optional[str]:
        """Extrae dirección de email de un texto usando regex."""
        matches = re.findall(self._email_pattern, text, re.IGNORECASE)
        for match in matches:
            if self._validate_email(match):
                return match.lower()
        return None

    def _clean_phone_number(self, phone: str) -> str:
        """Limpia y normaliza un número de teléfono."""
        # Remover caracteres no numéricos excepto + al inicio
        if phone.startswith('+'):
            clean = '+' + re.sub(r'[^\d]', '', phone[1:])
        else:
            clean = re.sub(r'[^\d]', '', phone)

        return clean

    def _validate_phone(self, phone: str) -> bool:
        """Valida un número de teléfono."""
        if not phone:
            return False

        try:
            # Intentar parsear como número de teléfono internacional
            parsed = phonenumbers.parse(phone, None)
            return phonenumbers.is_valid_number(parsed)
        except phonenumbers.NumberParseException:
            # Si falla el parsing internacional, verificar formato básico
            return bool(re.match(r'^\+?\d{10,15}$', phone))

    def _validate_email(self, email: str) -> bool:
        """Valida una dirección de email."""
        if not email:
            return False

        try:
            validate_email(email, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False

    def _validate_website(self, website: str) -> bool:
        """Valida una URL de website."""
        if not website:
            return False

        # Patrones básicos de URL
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return bool(url_pattern.match(website))

    def _normalize_website(self, website: str) -> Optional[str]:
        """Normaliza una URL de website."""
        if not website:
            return None

        website = website.strip()

        # Agregar protocolo si no tiene
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website

        # Validar la URL normalizada
        if self._validate_website(website):
            return website

        return None

    def _calculate_contact_score(self, contact_info: Dict[str, Any]) -> int:
        """Calcula un score de calidad de la información de contacto."""
        score = 0

        if contact_info.get('phone') and self._validate_phone(contact_info['phone']):
            score += 3  # Teléfono es el contacto más valioso

        if contact_info.get('email') and self._validate_email(contact_info['email']):
            score += 2  # Email es muy valioso

        if contact_info.get('website') and self._validate_website(contact_info['website']):
            score += 1  # Website es útil pero menos crítico

        return score